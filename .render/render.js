const fs = require("fs").promises;
const path = require("path");
const { marked } = require("marked");
const DOMPurify = require("dompurify");
const { JSDOM } = require("jsdom");
const yaml = require("js-yaml");
const crypto = require("crypto");

const REPO_ROOT = process.cwd();
const RENDER_ROOT = path.join(REPO_ROOT, ".render");
const OUTPUT_ROOT = path.join(REPO_ROOT, "_site");

// ================================
// Markdown renderer configuration
// ================================
marked.setOptions({
    headerIds: true,
    mangle: false,
    gfm: true,
    breaks: true,
    tables: true,
    highlight: function (code, lang) {
        return `<pre class="language-${lang}"><code class="language-${lang}">${escapeHtml(
            code
        )}</code></pre>`;
    },
});

// ================================
// Helpers (no side effects)
// ================================
/* Escape special HTML characters in a string. */
function escapeHtml(text) {
    const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
}

/* Recursively walk files under startDir (excluding hidden/system dirs) and invoke onFile for each file. */
async function walkFiles(startDir, onFile) {
    const excludeNames = new Set([
        ".git",
        ".github",
        ".render",
        "_site",
        "node_modules",
    ]);
    async function walk(dir) {
        const entries = await fs.readdir(dir, { withFileTypes: true });
        for (const entry of entries) {
            if (entry.name.startsWith(".")) continue;
            if (excludeNames.has(entry.name)) continue;
            const fullPath = path.join(dir, entry.name);
            if (entry.isDirectory()) {
                await walk(fullPath);
            } else if (entry.isFile()) {
                await onFile(fullPath);
            }
        }
    }
    await walk(startDir);
}

/* Collect absolute paths of .md files under startDir. */
async function findMarkdownFiles(startDir) {
    const results = [];
    await walkFiles(startDir, async (fullPath) => {
        if (/\.md$/i.test(fullPath)) results.push(fullPath);
    });
    return results;
}

/* Copy entire tree from startDir to outputDir, preserving structure. */
async function copyTree(startDir, outputDir) {
    await walkFiles(startDir, async (fullPath) => {
        const rel = path.relative(startDir, fullPath);
        const dest = path.join(outputDir, rel);
        await fs.mkdir(path.dirname(dest), { recursive: true });
        await fs.copyFile(fullPath, dest);
    });
}

/* Parse leading YAML frontmatter from markdown; returns {attributes, body}. */
function parseYamlFrontmatter(md) {
    const m = String(md).match(/^---\s*\n([\s\S]*?)\n---\s*\n?/);
    if (!m) return { attributes: {}, body: String(md) };
    let attributes = {};
    try {
        attributes = yaml.load(m[1]) || {};
    } catch {
        attributes = {};
    }
    const body = String(md).slice(m[0].length);
    return { attributes, body };
}

/* Extract the first H1 heading text from markdown or throw if none. */
function parseFirstH1(md) {
    const m = String(md).match(/^\s{0,3}#\s+(.+)$/m);
    if (!m) throw new Error("No H1 header found");
    return m[1].trim();
}

// ================================
// Simplified path handling
// ================================
/*
Map a source .md path to its output HTML file path. Examples:

- README.md -> _site/index.html (home page)
- foo.md -> _site/foo/index.html
- foo/index.md -> _site/foo/index.html
- foo/bar.md -> _site/foo/bar/index.html
- foo/bar/index.md -> _site/foo/bar/index.html
*/
function computeOutputHtmlPath(mdPath, homeMdBasename) {
    const rel = path.relative(REPO_ROOT, mdPath);
    const base = path.basename(rel);
    const dir = path.dirname(rel);

    // Home page special case
    if (dir === "." && base === homeMdBasename) {
        return path.join(OUTPUT_ROOT, "index.html");
    }

    // Index.md special case
    if (base === "index.md") {
        return path.join(OUTPUT_ROOT, dir, "index.html");
    }

    // Everything else becomes dir/name/index.html
    const name = base.replace(/\.md$/i, "");
    return path.join(
        OUTPUT_ROOT,
        dir === "." ? name : path.join(dir, name),
        "index.html"
    );
}

/*
Rewrite relative links/resources in rendered HTML:
- .md links are converted to their output paths (stripping index.html/.html for clean URLs)
- Non-markdown assets are rebased relative to repo root
- External links, mailto/tel, and hashes are left unchanged
*/
function rewriteLinksHtml(htmlContent, sourceMdPath, homeMdBasename) {
    const dom = new JSDOM(`<!DOCTYPE html><body>${htmlContent}</body>`);
    const document = dom.window.document;
    const sourceDir = path.dirname(sourceMdPath);

    // Process all links and resources
    document
        .querySelectorAll(
            "a[href], img[src], video[src], audio[src], source[src], link[href], script[src]"
        )
        .forEach((el) => {
            const attr = el.hasAttribute("href") ? "href" : "src";
            const raw = el.getAttribute(attr);
            if (!raw) return;

            // Skip external links and anchors
            if (/^(https?:)?\/\//i.test(raw)) return;
            if (/^(mailto:|tel:|#)/i.test(raw)) return;

            // Extract path without query/hash
            const [urlPath, ...rest] = raw.split(/[#?]/);
            const suffix = rest.length ? raw.slice(urlPath.length) : "";

            // Resolve target path
            const targetAbs = path.resolve(sourceDir, decodeURI(urlPath));
            const targetRel = path.relative(REPO_ROOT, targetAbs);

            // For .md files, compute output path and strip .html
            let newHref;
            if (/\.md$/i.test(urlPath)) {
                const targetOut = computeOutputHtmlPath(
                    targetAbs,
                    homeMdBasename
                );
                const sourceOut = computeOutputHtmlPath(
                    sourceMdPath,
                    homeMdBasename
                );
                newHref = path.relative(path.dirname(sourceOut), targetOut);
                // Strip index.html or .html for cleaner URLs
                newHref =
                    newHref
                        .replace(/\/index\.html$/, "")
                        .replace(/\.html$/, "") || ".";
            } else {
                // Non-markdown files stay as-is
                newHref = path.join(
                    "../".repeat(targetRel.split(path.sep).length - 1),
                    targetRel
                );
            }

            el.setAttribute(attr, newHref.split(path.sep).join("/") + suffix);
        });

    return document.body.innerHTML;
}

/* Copy template stylesheet to versioned asset path (content-hash) and return its destination path. */
async function copyStylesheet() {
    const src = path.join(RENDER_ROOT, "template", "style.css");
    const outDir = path.join(OUTPUT_ROOT, "assets");
    await fs.mkdir(outDir, { recursive: true });

    const css = await fs.readFile(src);
    const hash = crypto
        .createHash("sha1")
        .update(css)
        .digest("hex")
        .slice(0, 8);
    const dest = path.join(outDir, `style.${hash}.css`);
    await fs.writeFile(dest, css);
    return dest;
}

// ================================
// Simplified nav handling
// ================================
/*
Build normalized nav item descriptors from config.nav:
- Supports external URLs and internal markdown files/directories
- Derives titles from first H1 when omitted
- Computes each item's output HTML path
*/
async function buildNavItems(config, homeMdBasename) {
    const results = [];

    for (const item of config.nav) {
        let key, title;
        if (typeof item === "string") {
            key = item;
            title = null;
        } else {
            key = Object.keys(item)[0];
            title = item[key];
        }

        // External links
        if (/^(https?:)?\/\//i.test(key) || /^(mailto:|tel:)/i.test(key)) {
            results.push({ type: "external", href: key, title: title || key });
            continue;
        }

        // Markdown files
        if (/\.md$/i.test(key)) {
            const mdPath = path.join(REPO_ROOT, key);
            if (!title) {
                const raw = await fs.readFile(mdPath, "utf-8");
                title = parseFirstH1(raw);
            }
            results.push({
                type: "internal",
                mdPath,
                title,
                outPath: computeOutputHtmlPath(mdPath, homeMdBasename),
            });
            continue;
        }

        // Try as directory with README.md or index.md
        const dirPath = path.join(REPO_ROOT, key);
        for (const indexName of ["README.md", "index.md"]) {
            const indexPath = path.join(dirPath, indexName);
            try {
                await fs.access(indexPath);
                if (!title) {
                    const raw = await fs.readFile(indexPath, "utf-8");
                    title = parseFirstH1(raw);
                }
                results.push({
                    type: "internal",
                    mdPath: indexPath,
                    title,
                    outPath: computeOutputHtmlPath(indexPath, homeMdBasename),
                });
                break;
            } catch {}
        }
    }

    return results;
}

/* Render the site navigation HTML using the nav template. */
function buildNavHtml(
    navItems,
    currentOutPath,
    siteTitle,
    homeOutPath,
    navTemplate
) {
    const currentDir = path.dirname(currentOutPath);
    const homeHref =
        path
            .relative(currentDir, homeOutPath)
            .split(path.sep)
            .join("/")
            .replace(/(?:^|\/)index\.html$/, "") || ".";

    const links = navItems.map((item) => {
        if (item.type === "external") {
            return `<a href="${escapeHtml(
                item.href
            )}" target="_blank" rel="noopener noreferrer">${escapeHtml(
                item.title
            )}</a>`;
        }

        let href =
            path
                .relative(currentDir, item.outPath)
                .split(path.sep)
                .join("/")
                .replace(/(?:^|\/)index\.html$/, "") || ".";

        return `<a href="${href}">${escapeHtml(item.title)}</a>`;
    });

    const titleHtml = `<a href="${homeHref}" class="site-title">${escapeHtml(
        siteTitle
    )}</a>`;

    return navTemplate
        .replace("{{TITLE_HTML}}", titleHtml)
        .replace("{{LINKS_HTML}}", links.join(" "));
}

// ================================
// Main rendering
// ================================
/* Load and validate .render/config.yml; fills defaults and ensures required keys. */
async function loadConfig() {
    const configPath = path.join(REPO_ROOT, ".render", "config.yml");
    const raw = await fs.readFile(configPath, "utf-8");
    const cfg = yaml.load(raw) || {};

    if (!cfg.site_title) throw new Error("Missing site_title in config");
    if (!cfg.home_md) throw new Error("Missing home_md in config");
    if (!Array.isArray(cfg.nav)) cfg.nav = [];

    return cfg;
}

/*
Render a single markdown file to an HTML page:
- Parses frontmatter and title
- Converts markdown to sanitized HTML
- Rewrites links and injects nav/stylesheet into the template
- Writes the final HTML to the computed output path
*/
async function renderPage(mdPath, ctx) {
    const { template, purify, navItems, stylesheet, config, navTemplate } = ctx;
    const homeMdBasename = path.basename(config.home_md);

    // Parse markdown
    const raw = await fs.readFile(mdPath, "utf-8");
    const { attributes: frontmatter, body } = parseYamlFrontmatter(raw);

    // Convert to HTML
    let html = marked(body);
    html = purify.sanitize(html, {
        ADD_TAGS: ["iframe", "video", "audio", "source"],
        ADD_ATTR: [
            "target",
            "rel",
            "frameborder",
            "allowfullscreen",
            "autoplay",
            "controls",
        ],
        ALLOW_DATA_ATTR: true,
    });
    html = rewriteLinksHtml(html, mdPath, homeMdBasename);

    // Extract title with priority: frontmatter.title -> first H1 -> config.site_title
    let title;
    if (
        frontmatter &&
        typeof frontmatter.title === "string" &&
        frontmatter.title.trim()
    ) {
        title = String(frontmatter.title).trim();
    } else {
        try {
            title = parseFirstH1(body);
        } catch {
            title = config.site_title;
        }
    }

    // Extract description with priority: frontmatter.description -> title
    let description;
    if (
        frontmatter &&
        typeof frontmatter.description === "string" &&
        frontmatter.description.trim()
    ) {
        description = String(frontmatter.description).trim();
    } else {
        description = title;
    }

    // Build nav
    const pageOut = computeOutputHtmlPath(mdPath, homeMdBasename);
    const homeOut = computeOutputHtmlPath(
        path.join(REPO_ROOT, config.home_md),
        homeMdBasename
    );
    const nav = buildNavHtml(
        navItems,
        pageOut,
        config.site_title,
        homeOut,
        navTemplate
    );

    // Get stylesheet path
    const stylePath = path
        .relative(path.dirname(pageOut), stylesheet)
        .split(path.sep)
        .join("/");

    // Build final HTML
    const finalHtml = template
        .replace("{{TITLE}}", escapeHtml(title))
        .replace("{{DESCRIPTION}}", escapeHtml(description))
        .replace("{{NAV}}", nav)
        .replace("{{STYLESHEET_HREF}}", stylePath)
        .replace("{{CONTENT}}", html);

    // Write file
    await fs.mkdir(path.dirname(pageOut), { recursive: true });
    await fs.writeFile(pageOut, finalHtml);

    console.log(
        `✅ ${path.relative(REPO_ROOT, mdPath)} -> ${path.relative(
            REPO_ROOT,
            pageOut
        )}`
    );
}

/*
End-to-end site build:
- Loads template/config, copies stylesheet, builds nav, copies static files
- Renders all markdown files into the output directory
*/
async function buildSite() {
    // Load everything
    const template = await fs.readFile(
        path.join(RENDER_ROOT, "template", "index.html"),
        "utf-8"
    );
    const navTemplate = await fs.readFile(
        path.join(RENDER_ROOT, "template", "nav.html"),
        "utf-8"
    );
    const config = await loadConfig();
    const stylesheet = await copyStylesheet();
    const navItems = await buildNavItems(config, path.basename(config.home_md));
    const purify = DOMPurify(new JSDOM("").window);

    // Copy static files
    await copyTree(REPO_ROOT, OUTPUT_ROOT);

    // Render all markdown
    const mdFiles = await findMarkdownFiles(REPO_ROOT);
    for (const mdPath of mdFiles) {
        await renderPage(mdPath, {
            template,
            purify,
            navItems,
            stylesheet,
            config,
            navTemplate,
        });
    }

    console.log(`📁 Output: ${OUTPUT_ROOT}`);
}

buildSite();
