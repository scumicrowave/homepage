# Changjun Liu — Academic Homepage

Static, dependency-free English academic homepage for **GitHub Pages**. Publications are grouped by year in reverse chronological order, each with a PDF download button, and the full-text PDFs are hosted on the site itself.

> **Current status — deployed.** Live at https://scumicrowave.github.io/homepage/ (2026-11-13). Published through the GitHub Git Data API: 127 files / 211.6 MB in a single commit, with all 116 PDFs under `papers/`. Remote-only files were preserved (75 old files kept), so nothing was deleted.

> **Chinese edition — deployed on Tencent's free web hosting (WorkBuddy App Publishing).** Live at https://wbapp-8qepa8vil4cd5d2qpy9kii.apps.workbuddy.host/?sharecode=2RJXT4VKJN (2026-11-13). Built with `python build.py --lang zh` into `zh/`; it shares the same `publications.json` data, uses `profile_zh` for Chinese UI text, and links PDF downloads to the already-published English GitHub Pages site instead of duplicating the 211 MB of PDFs.

## What is on the page

- **71 publications**, 2015–2025, grouped by year (newest first), with type badges, DOI / Scholar / Mirror links and a searchable toolbar with year and type filters.
- **50 publications** point to a self-hosted PDF in `papers/`; entries without a direct PDF fall back to the public paper repository (`PDF †`).
- **116 full-text PDFs** in a searchable **PDF Repository** section, also grouped by year where the year can be confirmed.
- English profile, research interests, professional service, honors, books and contact details, plus schema.org `Person` metadata.
- No CDN, no build tools, no JavaScript required for the content; responsive and printable.

## Files

| Path | Purpose |
|---|---|
| `index.html` | Generated English site. Do not edit by hand. |
| `zh/index.html` | Generated Chinese site (deployed to Tencent free hosting). Do not edit by hand. |
| `publications.json` | **Single source of truth** — `profile` (English), `profile_zh` (Chinese), publications and the PDF library. Edit this. |
| `build.py` | Regenerates `index.html` (`python build.py`) or `zh/index.html` (`python build.py --lang zh`) from `publications.json` (Python standard library only). |
| `assets/style.css` | Styles. |
| `assets/app.js` | Search / filters for publications and the PDF repository (progressive enhancement). |
| `assets/photo.jpg` | Optional portrait. If absent, a monogram is shown. |
| `papers/` | 116 self-hosted PDFs (~211 MB). See `papers/README.md`. |
| `.nojekyll` | Tells GitHub Pages not to run Jekyll. |
| `_matches.json` | Intermediate title→PDF matching result used while building the library. |

## Add or fix a paper

1. Edit `publications.json`:
   ```json
   {"year":2026,"type":"journal","authors":"A. Author and C. Liu","title":"Paper Title","venue":"IEEE Trans. X, vol. 1, no. 2, pp. 3-9, 2026","doi":"10.1109/...","pdf":"https://.../paper.pdf"}
   ```
   - `type`: `journal` \| `conference` \| `magazine` \| `patent` \| `editorial` \| `book`
   - `doi` / `pdf` / `local` / `selected` are optional.
2. Regenerate both editions:
   ```bash
   python build.py            # English -> index.html
   python build.py --lang zh  # Chinese  -> zh/index.html (copies assets into zh/assets)
   ```
   Publication titles/authors/venues stay in English on both sites so they remain searchable and DOI-matchable; only the surrounding UI text and the profile are translated. The Chinese site keeps PDF links pointed at the published English site (`PDF_BASE` in `build.py`), so no PDF copies are needed in `zh/`.
3. Commit and push to GitHub for the English site; re-publish the `zh/` directory through the Tencent/WorkBuddy App Publishing tool for the Chinese site.

## Self-host a PDF

Put the file in `papers/` and add `"local": "papers/2026-01.pdf"` to the entry. `local` becomes the primary PDF link; any `pdf` URL is kept as a **Mirror** link. URLs are percent-encoded by `build.py`, so filenames with spaces or Chinese characters work.

The **PDF Repository** section is driven by `publications.json → full_pdf_library`, one record per file in `papers/`:

```json
{"title": "Paper title", "file": "papers/2024/....pdf", "year": 2024, "year_source": "publication"}
```

`year_source` is `publication` (matched to a publication record), `filename` (a dated folder/prefix such as `2023/`), or `unconfirmed`. **PDF file creation dates are deliberately not used as publication years** — many were rewritten during export and would mis-group dozens of papers. Unconfirmed files are collected in the final "Earlier works & undated full texts" group.

## Local preview

```bash
cd D:/Workbuddy/Claw
python -m http.server 8000
```

Open `http://localhost:8000`. No network or build tools required.

## Publish to GitHub

Target: the existing GitHub Pages repo **`scumicrowave/homepage`**, currently live at `https://scumicrowave.github.io/homepage/`. It already contains an older `index.html` and some PDFs. Replacing the homepage is approved; the script still keeps the remote-only files rather than deleting them.

### Recommended: REST API (`deploy_api.py`)

`git fetch/push` can stall behind proxies when uploading large binary files. The API deployer uploads blobs directly and creates one commit — 127 files / 211.6 MB in about two minutes:

```bash
GITHUB_TOKEN=ghp_xxx python deploy_api.py
```

It uses `base_tree` so remote-only files are preserved, and caches uploaded blob SHAs so an interrupted run can be resumed. Needs a repo-scoped PAT or a fine-grained token with **Contents: read + write** on `scumicrowave/homepage`.

### Alternative: git push (`deploy.sh`)

```bash
GITHUB_TOKEN=ghp_xxx bash deploy.sh
```

Initialises git, stages the site, replays everything as one commit on top of the existing remote history (no force-push, no unrelated-history errors), pushes, then strips the token from the stored remote URL. Remote-only files are kept. Use this when git-over-HTTPS is reliable.

### Manual equivalent

```bash
cd D:/Workbuddy/Claw
git init
git config user.name "Changjun Liu"
git config user.email "cjliu@scu.edu.cn"
git add .
git commit -m "Rebuild academic homepage with 116 self-hosted PDFs"
git branch -M main
git remote add origin https://github.com/scumicrowave/homepage.git
# first fetch the existing history so the push is not rejected:
git pull --rebase origin main
git push -u origin main
```

Authenticate with a GitHub personal access token (repo scope) when prompted, or set the remote URL to `https://<USER>:<PAT>@github.com/scumicrowave/homepage.git`. **Never commit the token** into any tracked file. If you explicitly want to discard the old homepage instead of merging, replace the last two lines with `git push -u origin main --force`.

If you create a fresh `<USERNAME>.github.io` repo instead, the site appears at `https://<USERNAME>.github.io/`; otherwise use `https://<USERNAME>.github.io/<REPO>/`. On GitHub: **Settings → Pages → Deploy from a branch → `main` / `root` → Save**. Update `profile.site_url` afterwards.

## Bind a custom domain

> **Not supported on the free Tencent/WorkBuddy hosting.** The Chinese edition currently lives at
> `https://wbapp-8qepa8vil4cd5d2qpy9kii.apps.workbuddy.host/?sharecode=2RJXT4VKJN`, a
> platform-assigned subdomain. That free one-click host (CloudStudio sandbox) has **no
> custom-domain option**; `domainPrefix` only requests a friendlier first segment when an app
> is first created, and re-publishing keeps the same link. Tencent **EdgeOne Pages** does support
> custom domains, but requires a Tencent Cloud account and an **ICP-filed (备案) domain**.

The cheapest permanent route is the GitHub Pages repo you already have
(`scumicrowave/homepage`): custom domains are free, stable and need no ICP filing. Bind one
domain and both language editions get friendly URLs:

| Site | URL after binding |
|---|---|
| English | `https://<domain>/` |
| Chinese | `https://<domain>/zh/` |
| PDF files | `https://<domain>/papers/...` (or keep the `github.io` absolute links) |

Steps:

1. Own a domain. Possible candidate from the profile: `mwpt.tech` (MWPT group) — confirm you
   control its DNS; a subdomain such as `cn.mwpt.tech` is fine. It did not resolve from this
   machine, so verify before use.
2. Add DNS records at your registrar (exact GitHub Pages values):
   - apex `@` → `A` `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - apex `@` → `AAAA` `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - `www` → `CNAME` `scumicrowave.github.io` — **never** include `/homepage` or the repo name
   - DNS may take up to 24 h; remove any default/wildcard records first.
3. In the repo, add a one-line `CNAME` file containing the chosen domain at the **root**, or let
   GitHub create it when you enter the domain under **Settings → Pages → Custom domain → Save**.
   Then enable **Enforce HTTPS**.
4. Keep the generated `zh/` directory in the repo so the Chinese site is served at `/zh/`.
   Update `profile.site_url`, optionally point `PDF_BASE` in `build.py` at the new domain, and
   rebuild both editions (`python build.py` and `python build.py --lang zh`).
5. Push with `GITHUB_TOKEN=ghp_xxx python deploy_api.py` (the GitHub connector is read-only).

**Pending before this can be finished:** the domain name, whether it is ICP-filed (decides
GitHub Pages vs EdgeOne Pages), and GitHub write authorization. DNS records must be added by
the domain owner at their registrar — that step cannot be done from here.

## Content sources

Profile and publication list compiled from the existing Google Sites homepage, IEEE Xplore author profile, IEEE MTT-S profile, Sichuan University EIE faculty page and Baidu Baike. Google Scholar blocked automated retrieval, so citation counts come from IEEE Xplore (138 publications / 2,043 citations). The 116 PDFs come from the exported Google Drive folder `Public research articles` supplied as a local zip.

### Known data issues / to confirm

- The source Google Sites page assigned the **same Google Drive placeholder link** to many 2024 entries and reused one link across two 2021 papers. Those were dropped rather than published as broken downloads.
- Google Scholar ID confirmed as **`_6js4T4AAAAJ`**; the `vTWbtXkAAAAJ` ID on the old homepage is stale. `profile.links` already uses the confirmed one.
- The publication list covers 2015–2025 (no 2016 entries on the source page); IEEE Xplore shows work up to 2026 — add newer papers.
- The PDF library contains 116 files (~211 MB); every file is under 18 MB, within GitHub's 100 MB per-file limit and 1 GB soft repo limit.
- **Verify every hosted PDF is legally shareable** (publisher copyright / open-access / accepted-manuscript status) before making the repository public.
- Deployed 2026-11-13 with a one-off PAT. **Revoke that token** after use; future updates can use either deployer.
