# quantem-docs

Documentation site for [quantEM](https://github.com/electronmicroscopy/quantem), built with [MyST Markdown](https://mystmd.org) (`mystmd` — no Sphinx) and the `book-theme` template with custom styling in `style.css`.

## Local preview

Requires Node.js ≥ 18.

```bash
npm install -g mystmd   # once
myst start              # live-reload dev server at http://localhost:3000
```

## Static build

```bash
myst build --html       # output in _build/html
```

## Deployment

Pushes to `main` build and deploy the site to GitHub Pages via `.github/workflows/deploy.yml`. Enable **Settings → Pages → Source: GitHub Actions** in the repository settings (one-time setup).

## Layout

- `myst.yml` — site config and table of contents
- `style.css` — custom theming (accent colors, light/dark tweaks)
- `assets/logo.svg` — animated logo (placeholder)
- `index.md` — landing page
- `get-started/`, `user-guide/`, `reference/`, `project/` — content pages

User Guide pages are condensed from the notebooks in [quantem-tutorials](https://github.com/electronmicroscopy/quantem-tutorials).
