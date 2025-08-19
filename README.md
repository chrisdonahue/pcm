# Markdown Publisher

Markdown Publisher (`md-pub`) is a simple template for deploying Markdown as static HTML via GitHub pages. A "keep it simple" alternative to things like Jekyll, Hugo, etc.

See the result of this example repo here: https://chrisdonahue.com/md-pub

## Features

- Clean Markdown structure, mirrored 1:1 in HTML
- Uses GitHub Actions to build and deploy the site to GitHub Pages
- Small, hackable JS codebase (see `.render` directory)
- Arbitrary static assets (images, etc.)
- Multiple pages, directories, [relative links](./lorem) and [anchors](#usage-instructions)
- YAML frontmatter metadata support
- MIT licensed

## Usage instructions

1. Fork the repository (probably change the repo name as well)
1. Go to settings and enable GitHub Pages via GitHub Actions
1. Edit the `README.md` (or any other markdown file) with your content
1. Edit `.render/config.yml` to your liking
1. Customize `.render/template` to your liking
1. Commit and push the changes
1. Wait for the GitHub Actions to build and deploy the site

### Testing locally

```sh
npm init -y
npm install marked jsdom dompurify js-yaml
node .render/render.js
python3 -m http.server --directory _site 8080
```

## Assets

Put your assets anywhere in the repo and use them as expected:

![Markdown Publisher Logo](./markdown.svg)
