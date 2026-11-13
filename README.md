# U.S. Construction Industry Intelligence — v4.0

A populated source-linked national executive dashboard with **Executive Overview**, **Historical Trends**, and **Data & Refresh**. Uses exactly 18 source entries from the user-approved November 12, 2026 document.

## What is truly live

- `scripts/collect.py` checks public website pages each day and publishes discovered article/report links to `data/latest.json`.
- GitHub Actions refreshes that research dataset and deploys the same dashboard URL.
- The numerical baseline consists of verified publisher-linked observations from November 12, 2026; automated numerical extraction **is not implemented**. Monthly historical points are charted only where independently reported. No made-up time series.
- Missing or blocked publishers are reported as unavailable, never assumed to report zero activity.

## Publish to GitHub (no coding required)

1. Create a GitHub account at https://github.com/signup (if needed).
2. Create a new **public** repository named `construction-intelligence`. Do not tick "Add a README".
3. Extract the downloaded zip on your PC. To preserve `.github/workflows` and `data`, upload the complete contents with a Git client such as GitHub Desktop, or add the workflows by creating files at exact paths in the web editor.
4. Go to **Settings → Pages → Build and deployment → Source → GitHub Actions**.
5. Under **Actions**, choose **Check approved construction sources → Run workflow**. The other workflow publishes the site on commits and after collection.
6. Open `https://YOUR-USERNAME.github.io/construction-intelligence/` after the Pages deploy succeeds.
7. In **Settings → Actions → General → Workflow permissions**, if necessary permit **Read and write permissions** so the collector can commit refreshed JSON.

**Important:** A GitHub Pages site published from a public repository is visible publicly. It must not contain proprietary business data.

Local opening of `index.html` shows all verified baseline figures but cannot run the scheduled collection job. Scheduled jobs are best effort: some sites reject automation, require subscriptions, or are inaccessible. Article counts do not indicate construction output. Numerical updates must be validated separately.
