# SupeRR Selector dashboard

This is a zero-build static dashboard. `index.html` loads `../dashboard_data.json` when served, while `fallback_data.js` keeps the same generated data available when the page is opened directly with `file://`.

## Deploy in one click

- **Vercel:** import this repository, set the project root to `dashboard`, leave the framework preset as “Other”, and deploy.
- **Netlify:** drag the `dashboard/` folder onto Netlify Drop, or set the publish directory to `dashboard`.
- **GitHub Pages:** push the folder to a repository, then enable Pages from the repository’s Actions/Pages settings.

The analysis script regenerates `fallback_data.js` whenever the shortlist changes.
