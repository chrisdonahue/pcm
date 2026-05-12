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

/* Apply ordered global string replacements (literal, not regex). */
function applyGlobalReplacements(input, replacements) {
    if (!Array.isArray(replacements) || replacements.length === 0) return input;
    let output = String(input);
    for (const pair of replacements) {
        if (
            !pair ||
            typeof pair.from !== "string" ||
            pair.from.length === 0 ||
            typeof pair.to !== "string"
        ) {
            continue;
        }
        // Literal replacement using split/join to avoid regex escaping pitfalls
        output = output.split(pair.from).join(pair.to);
    }
    return output;
}

/*
Make <audio>/<video> elements visible and surface their inner caption text:
- Add `controls` if missing (without it, the player has zero size and is invisible)
- Move inner content into a sibling <figcaption> wrapped in <figure>
  (inner content of <audio>/<video> is HTML5 fallback content, hidden in modern browsers)
- If the media is the only child of a <p>, replace the <p> entirely for cleaner HTML
*/
function enhanceMediaElements(htmlContent) {
    const dom = new JSDOM(`<!DOCTYPE html><body>${htmlContent}</body>`);
    const document = dom.window.document;

    document.querySelectorAll("audio, video").forEach((media) => {
        if (!media.hasAttribute("controls")) {
            media.setAttribute("controls", "");
        }

        const captionHtml = media.innerHTML.trim();
        if (!captionHtml) return;

        while (media.firstChild) media.removeChild(media.firstChild);

        const figure = document.createElement("figure");
        figure.className = media.tagName.toLowerCase() + "-figure";
        const figcaption = document.createElement("figcaption");
        figcaption.innerHTML = captionHtml;

        const parent = media.parentNode;
        if (
            parent &&
            parent.tagName === "P" &&
            parent.childNodes.length === 1
        ) {
            parent.parentNode.insertBefore(figure, parent);
            figure.appendChild(media);
            figure.appendChild(figcaption);
            parent.parentNode.removeChild(parent);
        } else if (parent) {
            parent.insertBefore(figure, media);
            figure.appendChild(media);
            figure.appendChild(figcaption);
        }
    });

    return document.body.innerHTML;
}

// Add id attributes to headings (simple deterministic slug)
function addHeadingIds(htmlContent) {
    const dom = new JSDOM(`<!DOCTYPE html><body>${htmlContent}</body>`);
    const document = dom.window.document;
    const used = new Set();
    function slugify(text) {
        return String(text || "")
            .toLowerCase()
            .replace(/<[^>]*>/g, "")
            .trim()
            .replace(/[^\w\s-]/g, "")
            .replace(/\s+/g, "-")
            .replace(/-+/g, "-");
    }
    document.querySelectorAll("h1,h2,h3,h4,h5,h6").forEach((h) => {
        const base = slugify(h.textContent);
        let id = base;
        let i = 1;
        while (id && used.has(id)) id = `${base}-${i++}`;
        if (id) {
            h.setAttribute("id", id);
            used.add(id);
        }
    });
    return document.body.innerHTML;
}

// ================================
// URL/path helpers (no side effects)
// ================================
function isExternalLink(raw) {
    return /^(https?:)?\/\//i.test(raw) || /^(mailto:|tel:)/i.test(raw);
}

function splitUrl(raw) {
    const hashIndex = raw.indexOf("#");
    const baseAndQuery = hashIndex >= 0 ? raw.slice(0, hashIndex) : raw;
    const anchorPart = hashIndex >= 0 ? raw.slice(hashIndex + 1) : "";
    const qIndex = baseAndQuery.indexOf("?");
    const pathPart = qIndex >= 0 ? baseAndQuery.slice(0, qIndex) : baseAndQuery;
    const queryPart = qIndex >= 0 ? baseAndQuery.slice(qIndex) : "";
    return { pathPart, queryPart, anchorPart };
}

function resolveAuthorPathAbs(authorPath, sourceDir) {
    return authorPath.startsWith("/")
        ? path.resolve(REPO_ROOT, "." + authorPath)
        : path.resolve(sourceDir, authorPath);
}

async function fileExists(p) {
    try {
        await fs.access(p);
        return true;
    } catch {
        return false;
    }
}

async function resolveMarkdownTargetAbs(candidateBaseAbs) {
    const candidates = /\.md$/i.test(candidateBaseAbs)
        ? [candidateBaseAbs]
        : [candidateBaseAbs + ".md", path.join(candidateBaseAbs, "index.md")];
    for (const c of candidates) {
        if (c.startsWith(REPO_ROOT) && (await fileExists(c))) return c;
    }
    return null;
}

function toOutputRelativeCleanUrl(targetOutPath, currentDir) {
    return (
        path
            .relative(currentDir, targetOutPath)
            .split(path.sep)
            .join("/")
            .replace(/(?:^|\/)index\.html$/, "") || "."
    );
}

function outputPathForStaticAsset(assetAbs) {
    const assetRelFromRepo = path.relative(REPO_ROOT, assetAbs);
    return path.join(OUTPUT_ROOT, assetRelFromRepo);
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

/*
If mdPath is a chapter index of the form `chapter/<N>-*\/index.md`, return the
chapter number N. Otherwise return null.
*/
function getChapterNumber(mdPath) {
    const rel = path.relative(REPO_ROOT, mdPath);
    const parts = rel.split(path.sep);
    if (parts.length !== 3) return null;
    if (parts[0] !== "chapter") return null;
    if (parts[2] !== "index.md") return null;
    const m = parts[1].match(/^(\d+)-/);
    return m ? parseInt(m[1], 10) : null;
}

/*
Prepend 0-indexed section numbers to ATX markdown headers in chapter index files.
- H1 -> "# (N) ..." where N is the chapter number
- H2 -> "## (N.x) ..." where x is the 0-indexed H2 count within the chapter
- H3 -> "### (N.x.y) ..." where y is the 0-indexed H3 count within the current H2
- ...and so on for deeper levels
Header detection skips fenced code blocks.
*/
function prependChapterSectionNumbers(body, chapterNum) {
    const lines = body.split("\n");
    let inFence = false;
    let fenceChar = null;
    const counts = {};

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        const fenceMatch = line.match(/^\s{0,3}(`{3,}|~{3,})/);
        if (fenceMatch) {
            const marker = fenceMatch[1][0];
            if (!inFence) {
                inFence = true;
                fenceChar = marker;
            } else if (marker === fenceChar) {
                inFence = false;
                fenceChar = null;
            }
            continue;
        }
        if (inFence) continue;

        const m = line.match(/^(#{1,6})\s+(.*)$/);
        if (!m) continue;
        const level = m[1].length;
        const rest = m[2];

        if (level === 1) {
            counts[1] = chapterNum;
            for (let k = 2; k <= 6; k++) delete counts[k];
            lines[i] = `${m[1]} (${chapterNum}) ${rest}`;
        } else {
            counts[level] = counts[level] === undefined ? 0 : counts[level] + 1;
            for (let k = level + 1; k <= 6; k++) delete counts[k];
            const parts = [];
            for (let k = 1; k <= level; k++) {
                parts.push(counts[k] === undefined ? 0 : counts[k]);
            }
            lines[i] = `${m[1]} (${parts.join(".")}) ${rest}`;
        }
    }

    return lines.join("\n");
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

    // Home page special cases
    // - Configured home page
    // - Conventional root README.md
    if (dir === "." && (base === homeMdBasename || base === "README.md")) {
        return path.join(OUTPUT_ROOT, "index.html");
    }

    // 404 page special case at repo root
    if (dir === "." && base === "404.md") {
        return path.join(OUTPUT_ROOT, "404.html");
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
Rewrite links/resources in rendered HTML:
- HREFs: rewrite internal links authored relative to the source .md so they point
  to the correct generated output (clean URLs, preserve anchors/queries)
- SRCs: rebase asset paths to the correct output location
- Skip external links and mailto/tel
*/
async function rebaseAssetSrcPaths(
    htmlContent,
    sourceMdPath,
    currentOutPath,
    homeMdBasename
) {
    const dom = new JSDOM(`<!DOCTYPE html><body>${htmlContent}</body>`);
    const document = dom.window.document;
    const sourceDir = path.dirname(sourceMdPath);
    const currentDir = path.dirname(currentOutPath);

    const nodes = Array.from(
        document.querySelectorAll(
            "a[href], img[src], video[src], audio[src], source[src], link[href], script[src]"
        )
    );

    for (const el of nodes) {
        const isHref = el.hasAttribute("href");
        const attr = isHref ? "href" : "src";
        const raw = el.getAttribute(attr);
        if (typeof raw !== "string" || raw.length === 0) continue;

        // Skip external links
        if (isExternalLink(raw)) continue;

        // Keep pure anchors as-authored
        if (raw.startsWith("#")) continue;

        const parts = splitUrl(raw);
        let pathPart = parts.pathPart;
        const queryPart = parts.queryPart;
        const anchorPart = parts.anchorPart;

        const decodedPath = decodeURI(pathPart);

        // Adjust paths
        if (isHref) {
            const candidateBaseAbs = resolveAuthorPathAbs(
                decodedPath,
                sourceDir
            );
            const mdTargetAbs = await resolveMarkdownTargetAbs(
                candidateBaseAbs
            );

            if (mdTargetAbs) {
                const outPath = computeOutputHtmlPath(
                    mdTargetAbs,
                    homeMdBasename
                );
                pathPart = toOutputRelativeCleanUrl(outPath, currentDir);
            } else {
                const assetAbs = resolveAuthorPathAbs(decodedPath, sourceDir);
                if (assetAbs.startsWith(REPO_ROOT)) {
                    const assetOutPath = outputPathForStaticAsset(assetAbs);
                    pathPart = path
                        .relative(currentDir, assetOutPath)
                        .split(path.sep)
                        .join("/");
                }
            }
        } else {
            const assetAbs = resolveAuthorPathAbs(decodedPath, sourceDir);
            const assetOutPath = outputPathForStaticAsset(assetAbs);
            pathPart = path
                .relative(currentDir, assetOutPath)
                .split(path.sep)
                .join("/");
        }

        // Reconstruct without modifying the anchor
        const hash = anchorPart ? "#" + anchorPart : "";
        let newValue = pathPart + queryPart + hash;
        if (newValue === "" && isHref) newValue = ".";

        el.setAttribute(attr, newValue);
    }

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
Build nav items strictly from config.nav using { Title: "href" } mapping:
- href: external URL (http/https, mailto, tel) or .md file path
- title: used as-is
*/
async function buildNavItems(config, homeMdBasename) {
    const results = [];
    for (const item of config.nav) {
        if (!item || typeof item !== "object") {
            throw new Error(
                'config.nav items must be objects like { Title: "href" }'
            );
        }

        const title = Object.keys(item)[0];
        const href = item[title];

        if (typeof title !== "string" || !title.trim()) {
            throw new Error("config.nav item is missing a non-empty title key");
        }
        if (typeof href !== "string" || !href.trim()) {
            throw new Error(
                `config.nav item '${title}' is missing a non-empty href value`
            );
        }

        // External links
        if (/^(https?:)?\/\//i.test(href) || /^(mailto:|tel:)/i.test(href)) {
            results.push({ type: "external", href, title });
            continue;
        }

        // Internal markdown files only
        if (/\.md$/i.test(href)) {
            const mdPath = path.join(REPO_ROOT, href);
            results.push({
                type: "internal",
                mdPath,
                title,
                outPath: computeOutputHtmlPath(mdPath, homeMdBasename),
            });
            continue;
        }

        throw new Error(
            `config.nav item '${title}' has unsupported href '${href}'. Use a .md file path or an external URL.`
        );
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
    if (!Array.isArray(cfg.variables)) cfg.variables = [];

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
    const {
        template,
        purify,
        navItems,
        stylesheet,
        config,
        navTemplate,
        globalReplacements,
    } = ctx;
    const homeMdBasename = path.basename(config.home_md);

    // Parse markdown
    const raw = await fs.readFile(mdPath, "utf-8");
    // Apply global replacements BEFORE any parsing (frontmatter included)
    const preprocessed = applyGlobalReplacements(raw, globalReplacements);
    const { attributes: frontmatter, body } =
        parseYamlFrontmatter(preprocessed);

    // For chapter index files, prepend section numbers to headers before rendering.
    // The original `body` is preserved for title extraction below.
    const chapterNum = getChapterNumber(mdPath);
    const renderedBody =
        chapterNum !== null
            ? prependChapterSectionNumbers(body, chapterNum)
            : body;

    // Convert to HTML
    let html = marked(renderedBody);

    // Configure DOMPurify to preserve IDs on headings
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
        // Allow ID attribute on all elements (especially headings)
        ALLOWED_ATTR: [
            "href",
            "title",
            "id",
            "class",
            "src",
            "alt",
            "target",
            "rel",
            "frameborder",
            "allowfullscreen",
            "autoplay",
            "controls",
            "width",
            "height",
        ],
    });

    // Compute current page output path to correctly rebase assets
    const pageOut = computeOutputHtmlPath(mdPath, homeMdBasename);

    // Add heading ids and rebase asset src paths
    html = addHeadingIds(html);
    html = await rebaseAssetSrcPaths(html, mdPath, pageOut, homeMdBasename);
    html = enhanceMediaElements(html);

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

// (Removed helper; 404 is now rendered from 404.md like any other page)

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
    // Build ordered replacements from config.variables (list of single-entry maps)
    const globalReplacements = [];
    if (Array.isArray(config.variables)) {
        for (const entry of config.variables) {
            if (entry && typeof entry === "object") {
                const key = Object.keys(entry)[0];
                const val = entry[key];
                if (typeof key === "string" && typeof val === "string") {
                    globalReplacements.push({ from: key, to: val });
                }
            }
        }
    }

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
            globalReplacements,
        });
    }

    console.log(`📁 Output: ${OUTPUT_ROOT}`);

    // 404 will be generated from root 404.md if present
}

buildSite();
