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

async function findMarkdownFiles(startDir) {
    const results = [];
    await walkFiles(startDir, async (fullPath) => {
        if (/\.md$/i.test(fullPath)) results.push(fullPath);
    });
    return results;
}

async function copyTree(startDir, outputDir) {
    await walkFiles(startDir, async (fullPath) => {
        const rel = path.relative(startDir, fullPath);
        const dest = path.join(outputDir, rel);
        await fs.mkdir(path.dirname(dest), { recursive: true });
        await fs.copyFile(fullPath, dest);
    });
}

function parseYamlFrontmatter(md) {
    // YAML frontmatter delimited by --- at the very top
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

function parseFirstH1(md) {
    // Allow up to 3 leading spaces before the '#', per CommonMark ATX heading rules
    const m = String(md).match(/^\s{0,3}#\s+(.+)$/m);
    if (!m) throw new Error("No H1 header found");
    return m[1].trim();
}

// ================================
// Helpers (global state)
// ================================
function computeOutputHtmlPath(mdPath, homeMdBasename) {
    // Examples:
    // README.md -> _site/index.html
    // foo.md -> _site/foo/index.html
    // foo/index.md -> _site/foo/index.html
    // foo/bar.md -> _site/foo/bar/index.html
    // foo/bar/index.md -> _site/foo/bar/index.html
    const rel = path.relative(REPO_ROOT, mdPath);
    const base = path.basename(rel);
    const dir = path.dirname(rel);
    if (dir === "." && base === homeMdBasename) {
        return path.join(OUTPUT_ROOT, "index.html");
    }
    const name = base.replace(/\.md$/i, "");
    return path.join(
        OUTPUT_ROOT,
        dir === "." ? name : path.join(dir, name),
        "index.html"
    );
}

function toRelativeHref(fromDir, toFile) {
    let rel = path.relative(fromDir, toFile).split(path.sep).join("/");
    if (rel === "") rel = "index.html";
    return rel;
}

function toExtensionlessPath(href) {
    let out = href;
    // Remove trailing "index" or "index.html" at the end of the path (with or without preceding slash)
    out = out.replace(/(?:^|\/)index(?:\.html)?$/i, (m) =>
        m.startsWith("/") ? "" : ""
    );
    // Strip a remaining trailing .html if present (e.g., foo.html -> foo)
    out = out.replace(/\.html$/i, "");
    return out;
}

function rewriteLinksHtml(htmlContent, sourceMdPath, homeMdBasename) {
    const dom = new JSDOM(`<!DOCTYPE html><body>${htmlContent}</body>`);
    const document = dom.window.document;
    const sourceOutDir = path.dirname(
        computeOutputHtmlPath(sourceMdPath, homeMdBasename)
    );
    const processAttr = (el, attrName) => {
        const raw = el.getAttribute(attrName);
        if (!raw) return;
        if (/^(https?:)?\/\//i.test(raw)) return;
        if (/^(mailto:|tel:)/i.test(raw)) return;
        if (raw.startsWith("#")) return;
        let url = raw;
        let hash = "";
        let query = "";
        const hashIdx = url.indexOf("#");
        if (hashIdx >= 0) {
            hash = url.slice(hashIdx);
            url = url.slice(0, hashIdx);
        }
        const queryIdx = url.indexOf("?");
        if (queryIdx >= 0) {
            query = url.slice(queryIdx);
            url = url.slice(0, queryIdx);
        }
        const resolvedTarget = path.resolve(
            path.dirname(sourceMdPath),
            decodeURI(url)
        );
        let targetOutputAbs;
        if (/\.md$/i.test(url)) {
            targetOutputAbs = computeOutputHtmlPath(
                resolvedTarget,
                homeMdBasename
            );
        } else {
            const rel = path.relative(REPO_ROOT, resolvedTarget);
            targetOutputAbs = path.join(OUTPUT_ROOT, rel);
        }
        let relativeHref = toRelativeHref(sourceOutDir, targetOutputAbs);
        if (/\.md$/i.test(url)) {
            relativeHref = toExtensionlessPath(relativeHref);
            if (relativeHref === "") relativeHref = ".";
        }
        relativeHref = relativeHref + query + hash;
        el.setAttribute(attrName, relativeHref);
    };
    document.querySelectorAll("a[href]").forEach((a) => processAttr(a, "href"));
    document
        .querySelectorAll(
            "img[src], video[src], audio[src], source[src], link[href], script[src]"
        )
        .forEach((el) => {
            if (el.hasAttribute("src")) processAttr(el, "src");
            if (el.hasAttribute("href")) processAttr(el, "href");
        });
    return document.body.innerHTML;
}

async function copyStylesheet() {
    const src = path.join(RENDER_ROOT, "template", "style.css");
    const outDir = path.join(OUTPUT_ROOT, "assets");
    await fs.mkdir(outDir, { recursive: true });
    try {
        const css = await fs.readFile(src);
        const hash = crypto
            .createHash("sha1")
            .update(css)
            .digest("hex")
            .slice(0, 8);
        const filename = `style.${hash}.css`;
        const dest = path.join(outDir, filename);
        await fs.writeFile(dest, css);
        return dest;
    } catch {
        return null;
    }
}

async function readTemplate(templateFilename) {
    const templatePath = path.join(RENDER_ROOT, "template", templateFilename);
    return fs.readFile(templatePath, "utf-8");
}

function buildConfiguredTitleMap(nav) {
    const byBase = {};
    const byFullRel = {};
    const byDir = {};
    const isExternal = (key) =>
        /^(https?:)?\/\//i.test(key) || /^(mailto:|tel:)/i.test(key);
    const normalize = (p) => p.replace(/\\/g, "/").replace(/^\.\//, "");
    const normalizeDir = (p) => normalize(p).replace(/\/$/, "");
    for (const item of nav) {
        if (item && typeof item === "object") {
            const key = Object.keys(item)[0];
            const title = String(item[key]);
            byBase[path.basename(key)] = title;
            if (!isExternal(key)) {
                if (/\.md$/i.test(key)) {
                    byFullRel[normalize(key)] = title;
                } else {
                    // Treat as directory key
                    byDir[normalizeDir(key)] = title;
                }
            }
        }
    }
    return { byBase, byFullRel, byDir };
}

async function buildNavItems(config, homeMdBasename) {
    async function resolveMdNavItem(mdPathAbs, providedTitle) {
        let title = providedTitle ? String(providedTitle) : null;
        if (!title) {
            try {
                const raw = await fs.readFile(mdPathAbs, "utf-8");
                title = parseFirstH1(raw);
            } catch {
                const isHome =
                    path.basename(mdPathAbs) === homeMdBasename &&
                    path.dirname(mdPathAbs) === REPO_ROOT;
                title = isHome
                    ? "Home"
                    : path.basename(mdPathAbs).replace(/\.md$/i, "");
            }
        }
        return {
            type: "internal",
            mdPath: mdPathAbs,
            title,
            outPath: computeOutputHtmlPath(mdPathAbs, homeMdBasename),
        };
    }

    async function resolveDirKey(dirKey, providedTitle) {
        const dirAbs = path.join(REPO_ROOT, dirKey);
        try {
            const stat = await fs.stat(dirAbs);
            if (!stat.isDirectory()) return null;
            const readme = path.join(dirAbs, "README.md");
            const index = path.join(dirAbs, "index.md");
            try {
                await fs.access(readme);
                return await resolveMdNavItem(readme, providedTitle);
            } catch {}
            try {
                await fs.access(index);
                return await resolveMdNavItem(index, providedTitle);
            } catch {}
        } catch {}
        return null;
    }

    const entries = config.nav
        .map((item) => {
            if (typeof item === "string") return { key: item, title: null };
            if (item && typeof item === "object") {
                const key = Object.keys(item)[0];
                return { key, title: item[key] };
            }
            return null;
        })
        .filter(Boolean);

    const results = [];
    for (const entry of entries) {
        const key = entry.key;
        const providedTitle = entry.title;
        const isExternal =
            /^(https?:)?\/\//i.test(key) || /^(mailto:|tel:)/i.test(key);
        if (isExternal) {
            results.push({
                type: "external",
                href: key,
                title: providedTitle ? String(providedTitle) : key,
            });
            continue;
        }
        if (/\.md$/i.test(key)) {
            const mdPathAbs = path.join(REPO_ROOT, key);
            results.push(await resolveMdNavItem(mdPathAbs, providedTitle));
            continue;
        }
        const dirResolved = await resolveDirKey(key, providedTitle);
        if (dirResolved) {
            results.push(dirResolved);
            continue;
        }
        // Fallback: external href as-is
        results.push({
            type: "external",
            href: key,
            title: providedTitle ? String(providedTitle) : key,
        });
    }
    return results;
}

function buildNavHtml(
    navItems,
    currentOutDir,
    siteTitle,
    homeOutPathAbsolute,
    navTemplateContent
) {
    const links = navItems.map((item) => {
        if (item.type === "external") {
            return `<a href="${escapeHtml(
                item.href
            )}" style="margin-right:12px;" target="_blank" rel="noopener noreferrer">${escapeHtml(
                item.title
            )}</a>`;
        } else {
            const hrefFile = toRelativeHref(currentOutDir, item.outPath);
            const href = toExtensionlessPath(hrefFile);
            return `<a href="${href}" style="margin-right:12px;">${escapeHtml(
                item.title
            )}</a>`;
        }
    });
    const homeHrefFile = toRelativeHref(currentOutDir, homeOutPathAbsolute);
    let homeHref = toExtensionlessPath(homeHrefFile);
    if (homeHref === "") homeHref = ".";
    const titleHtml = siteTitle
        ? `<a href="${homeHref}" class="site-title">${escapeHtml(
              siteTitle
          )}</a>`
        : "";
    let tpl = navTemplateContent || "";
    // Provide multiple placeholders for flexibility
    tpl = tpl.replace("{{TITLE_HTML}}", titleHtml);
    tpl = tpl.replace("{{LINKS_HTML}}", links.join(" "));
    tpl = tpl.replace("{{HOME_HREF}}", homeHref);
    tpl = tpl.replace("{{SITE_TITLE}}", escapeHtml(siteTitle || ""));
    return tpl;
}

// ================================
// Main rendering functions
// ================================
async function loadConfig() {
    const configPath = path.join(REPO_ROOT, ".render", "config.yml");
    const raw = await fs.readFile(configPath, "utf-8");
    const cfg = yaml.load(raw) || {};
    if (typeof cfg.site_title !== "string")
        throw new Error(
            ".render/config.yml missing required string: site_title"
        );
    if (typeof cfg.home_md !== "string")
        throw new Error(".render/config.yml missing required string: home_md");
    if (!Array.isArray(cfg.nav))
        throw new Error(
            ".render/config.yml missing required array: nav (can be empty)"
        );
    return cfg;
}

async function renderPage(mdPath, ctx) {
    const {
        templateContent,
        purify,
        navItems,
        stylesheetOut,
        navTemplateContent,
        config,
    } = ctx;
    const homeMdBasename = path.basename(config.home_md);
    const rawMarkdown = await fs.readFile(mdPath, "utf-8");
    const { attributes: frontmatter, body: markdownContent } =
        parseYamlFrontmatter(rawMarkdown);
    let htmlContent = marked(markdownContent);
    htmlContent = purify.sanitize(htmlContent, {
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
    htmlContent = rewriteLinksHtml(htmlContent, mdPath, homeMdBasename);
    const h1Match = markdownContent.match(/^\s{0,3}#\s+(.+)$/m);
    const firstH1 = h1Match ? h1Match[1].trim() : "";
    const fallback = firstH1 || config.site_title || "";
    const title =
        frontmatter &&
        typeof frontmatter.title === "string" &&
        frontmatter.title.trim()
            ? frontmatter.title.trim()
            : fallback;
    const description =
        frontmatter &&
        typeof frontmatter.description === "string" &&
        frontmatter.description.trim()
            ? frontmatter.description.trim()
            : fallback;
    const pageOutputPath = computeOutputHtmlPath(mdPath, homeMdBasename);
    const homeOutPathAbsolute = computeOutputHtmlPath(
        path.join(REPO_ROOT, config.home_md),
        homeMdBasename
    );
    const navHtml = navItems.length
        ? buildNavHtml(
              navItems,
              path.dirname(pageOutputPath),
              config.site_title,
              homeOutPathAbsolute,
              navTemplateContent
          )
        : "";
    const stylesheetHref = stylesheetOut
        ? toRelativeHref(path.dirname(pageOutputPath), stylesheetOut).replace(
              /\\/g,
              "/"
          )
        : "";
    let finalHtml = templateContent
        .replace("{{TITLE}}", escapeHtml(title))
        .replace("{{DESCRIPTION}}", escapeHtml(description))
        .replace("{{NAV}}", navHtml)
        .replace("{{STYLESHEET_HREF}}", stylesheetHref)
        .replace("{{CONTENT}}", htmlContent);

    // No dynamic style injection; colors are defined in the stylesheet
    await fs.mkdir(path.dirname(pageOutputPath), { recursive: true });
    await fs.writeFile(pageOutputPath, finalHtml);
    console.log(
        `✅ Built: ${path.relative(REPO_ROOT, mdPath)} -> ${path.relative(
            REPO_ROOT,
            pageOutputPath
        )}`
    );
}

async function buildSite() {
    const templateContent = await readTemplate("index.html");
    const navTemplateContent = await readTemplate("nav.html");
    const config = await loadConfig();
    const homeMdBasename = path.basename(config.home_md);
    const stylesheetOut = await copyStylesheet();
    await copyTree(REPO_ROOT, OUTPUT_ROOT);
    const allMarkdownFiles = await findMarkdownFiles(REPO_ROOT);
    const navItems = await buildNavItems(config, homeMdBasename);
    const configuredTitleMap = buildConfiguredTitleMap(config.nav);
    const homeAbs = path.join(REPO_ROOT, config.home_md);
    const homeOutPathAbsolute = computeOutputHtmlPath(homeAbs, homeMdBasename);
    const purify = DOMPurify(new JSDOM("").window);
    for (const mdPath of allMarkdownFiles) {
        await renderPage(mdPath, {
            templateContent,
            purify,
            navItems,
            stylesheetOut,
            navTemplateContent,
            config,
        });
    }
    console.log("📁 Output directory:", OUTPUT_ROOT);
    console.log(
        navItems.length
            ? `🧭 Pages in nav: ${navItems.map((n) => n.title).join(", ")}`
            : "🧭 No nav configured"
    );
}

buildSite();
