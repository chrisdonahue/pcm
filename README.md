# Markdown Publisher

Markdown Publisher (`md-pub`) is a simple template for deploying Markdown as static HTML via GitHub pages. A "keep it simple" alternative to things like Jekyll, Hugo, etc.

## Features

- Clean Markdown structure, mirrored 1:1 in HTML
- Uses GitHub Actions to build and deploy the site to GitHub Pages
- Tiny, hackable codebase (`.render`)
- Arbitrary static assets (images, etc.)
- Multiple pages, directories, relative links
- YAML frontmatter metadata support
- MIT licensed

## Usage

1. Fork the repository (probably change the repo name as well)
1. Go to settings and enable GitHub Pages via GitHub Actions
1. Edit the `README.md` (or any other markdown file) with your content
1. Edit `.render/config.yml` to your liking
1. Customize `.render/template` to your liking
1. Commit and push the changes
1. Wait for the GitHub Actions to build and deploy the site

## Assets

Put your assets anywhere in the repo and use them as expected:

![Markdown Publisher Logo](./markdown.svg)
