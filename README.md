# Changjun Liu — Academic Homepage

Static, dependency-free English academic homepage for **GitHub Pages**. Publications are grouped by year in reverse chronological order, each with a PDF download button, and the full-text PDFs are hosted on the site itself.

> **Current status — deployed.** Live at https://scumicrowave.github.io/homepage/ (2026-11-13). Published through the GitHub Git Data API: 127 files / 211.6 MB in a single commit, with all 116 PDFs under `papers/`. Remote-only files were preserved (75 old files kept), so nothing was deleted.

## What is on the page

- **71 publications**, 2015–2025, grouped by year (newest first), with type badges, DOI / Scholar / Mirror links and a searchable toolbar with year and type filters.
- **50 publications** point to a self-hosted PDF in `papers/`; entries without a direct PDF fall back to the public paper repository (`PDF †`).
- **116 full-text PDFs** in a searchable **PDF Repository** section, also grouped by year where the year can be confirmed.
- English profile, research interests, professional service, honors, books and contact details, plus schema.org `Person` metadata.
- No CDN, no build tools, no JavaScript required for the content; responsive and printable.

## Files

| Path | Purpose |
|---|---|
| `index.html` | Generated site. Do not edit by hand. |
| `publications.json` | **Single source of truth** — profile, publications and the PDF library. Edit this. |
| `build.py` | Regenerates `index.html` from `publications.json` (Python standard library only). |
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
2. Regenerate: `python build.py`
3. Commit and push.

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

Custom domain: add a `CNAME` file containing the domain (one line), set the DNS record, then update `profile.site_url`.

## Content sources

Profile and publication list compiled from the existing Google Sites homepage, IEEE Xplore author profile, IEEE MTT-S profile, Sichuan University EIE faculty page and Baidu Baike. Google Scholar blocked automated retrieval, so citation counts come from IEEE Xplore (138 publications / 2,043 citations). The 116 PDFs come from the exported Google Drive folder `Public research articles` supplied as a local zip.

### Known data issues / to confirm

- The source Google Sites page assigned the **same Google Drive placeholder link** to many 2024 entries and reused one link across two 2021 papers. Those were dropped rather than published as broken downloads.
- Google Scholar ID confirmed as **`_6js4T4AAAAJ`**; the `vTWbtXkAAAAJ` ID on the old homepage is stale. `profile.links` already uses the confirmed one.
- The publication list covers 2015–2025 (no 2016 entries on the source page); IEEE Xplore shows work up to 2026 — add newer papers.
- The PDF library contains 116 files (~211 MB); every file is under 18 MB, within GitHub's 100 MB per-file limit and 1 GB soft repo limit.
- **Verify every hosted PDF is legally shareable** (publisher copyright / open-access / accepted-manuscript status) before making the repository public.
- Deployed 2026-11-13 with a one-off PAT. **Revoke that token** after use; future updates can use either deployer.
