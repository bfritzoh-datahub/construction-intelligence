# Construction Intelligence v5.0 — Numeric Update Patch

This patch installs numerical extraction into your **existing** GitHub repository, `construction-intelligence`. It retains the existing 18 approved source entries and November 12 baseline.

## Install on Windows (GitHub Desktop)

1. Download `Construction_Intelligence_Numeric_Update_v5.zip` and select **Extract All**.
2. In GitHub Desktop, select `construction-intelligence`, then **Repository → Show in Explorer**. Confirm the location is `C:\GitHub\construction-intelligence`.
3. In the extracted ZIP, open the folder containing `index.html`, `scripts`, `.github`, `data`, `tests` and `requirements.txt`. **Copy those items**, not the enclosing ZIP folder.
4. Paste into `C:\GitHub\construction-intelligence`. If Windows asks, select **Replace the files in the destination** (only these application files). Do **not** delete the existing `.git` folder or the existing `sources.json`.
5. In GitHub Desktop → **Changes**, enter summary `Add validated ABC Dodge AIA numerical updates` and click **Commit to main**, then **Push origin**.
6. On GitHub in Chrome, click **Actions → Check approved construction sources → Run workflow** (branch `main`). Confirm green checkmark.
7. Click **Actions → Publish construction dashboard** and confirm it runs successfully, then open your existing GitHub Pages address and click **Data & Refresh → Reload published updates**.

## What this patch actually does

- Maintains existing report link discovery across all 18 approved entries.
- Adds conservative, rule-validated extraction for ABC contractor backlog, Dodge Momentum Index, Dodge total construction starts (annualized value and published YTD percentage), and AIA Architecture Billings Index from public publisher releases.
- Requires an approved publisher domain, appropriate release headline, explicit reporting month/year, a machine-readable publication date, one unambiguous numerical statement, valid units and a plausible range.
- Stores source URL, period, publication date and a short evidence span for every accepted record in `data/numeric_updates.json`.
- Re-checks reports daily. Never removes old accepted figures when a source is unavailable and does not overwrite a more recently published correction with an older record.
- Publishes the updated JSON with the daily workflow. The web dashboard loads it dynamically; no new HTML file download is needed for routine updates.
- Adds automated parser tests that run before the daily collector.

## Limits

- **The numerical collector has been tested against representative report text, not live end-to-end on GitHub.** Inspect the initial `numeric_updates.json` audit to see which exact publisher pages were accessible.
- Some publishers block automated requests; reports without suitable machine-readable dates or consistent phrasing will be rejected. That is intentional.
- The sources other than ABC, AIA and Dodge are still monitored for research links, not automatically numerically extracted.
- Not a licensed project-level data feed, not 10 years of historical numeric data, and not a calculation of actual quarter-dollar or YTD-dollar amounts.
- Automated rule validation is **not equivalent to human verification**. For high-stakes decisions, follow the source URL and review the published figure.
- A public GitHub repository exposes the application files and numerical records publicly. No secrets or credentials are used in this patch.
