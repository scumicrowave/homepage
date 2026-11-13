# Changjun Liu — Academic Homepage

Static, dependency-free English academic homepage for **GitHub Pages**. Publications are grouped by year in reverse chronological order, each with a PDF download button, and the full-text PDFs are hosted on the site itself.

> **Current status — BOTH language editions are served by GitHub Pages** (deployed 2026-11-13).
>
> | Edition | URL |
> |---|---|
> | English | https://scumicrowave.github.io/homepage/ |
> | Chinese | https://scumicrowave.github.io/homepage/zh/ |
> | PDFs | https://scumicrowave.github.io/homepage/papers/... (116 files) |
>
> Published through the GitHub Git Data API: 134 files / 211.8 MB in one commit, with all 116 PDFs under `papers/`. `base_tree` preserves remote-only files (220 blobs total), so nothing was deleted. A single repo now serves both languages — no second host, no duplicated PDF copies.

> **Legacy mirror.** The Chinese edition was also published on Tencent/WorkBuddy free hosting at https://wbapp-8qepa8vil4cd5d2qpy9kii.apps.workbuddy.host/?sharecode=2RJXT4VKJN . That host needs a `sharecode`, returns 403 without it, and **cannot be indexed by Google** — it is kept only as a fallback. The canonical Chinese site is the GitHub Pages `/zh/` URL above.

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
| `zh/index.html`, `zh/assets/` | Generated Chinese site + copied assets. Do not edit by hand. |
| `publications.json` | **Single source of truth** — `profile` (English), `profile_zh` (Chinese), publications, PDF library, and optional `google_site_verification`. Edit this. |
| `build.py` | Regenerates `index.html` (`python build.py`) or `zh/index.html` (`python build.py --lang zh`). Standard library only. |
| `seo.py` | Generates `robots.txt` and `sitemap.xml` (2 pages + 116 PDFs) from `site_url`. Re-run after a domain change. |
| `robots.txt`, `sitemap.xml` | Crawl directives + URL inventory for search engines. |
| `bind_domain.py` | Optional custom-domain binder (dry-run by default; `--apply` writes `CNAME`, updates URLs, rebuilds everything). |
| `deploy_api.py` | Uploads the whole site in one commit via the GitHub Git Data API. |
| `deploy.sh` | Alternative git-push deployer. |
| `assets/style.css` | Styles. |
| `assets/app.js` | Search / filters for publications and the PDF repository (progressive enhancement). |
| `assets/photo.jpg` | Optional portrait. If absent, a monogram is shown. |
| `papers/` | 116 self-hosted PDFs (~211 MB). See `papers/README.md`. |
| `.nojekyll` | Tells GitHub Pages not to run Jekyll. |
| `google89b0777337e2a7d8.html` | **Google Search Console ownership verification file. Never delete** — see below. |
| `_matches.json` | Intermediate title→PDF matching result used while building the library. |

## Add or fix a paper

1. Edit `publications.json`:
   ```json
   {"year":2026,"type":"journal","authors":"A. Author and C. Liu","title":"Paper Title","venue":"IEEE Trans. X, vol. 1, no. 2, pp. 3-9, 2026","doi":"10.1109/...","pdf":"https://.../paper.pdf"}
   ```
   - `type`: `journal` \| `conference` \| `magazine` \| `patent` \| `editorial` \| `book`
   - `doi` / `pdf` / `local` / `selected` are optional.
2. Regenerate both editions **and** the SEO files, then deploy everything in one commit:
   ```bash
   python build.py            # English -> index.html
   python build.py --lang zh  # Chinese  -> zh/index.html (copies assets into zh/assets)
   python seo.py              # robots.txt + sitemap.xml
   python deploy_api.py       # one commit, all 134 files
   ```
   Publication titles/authors/venues stay in English on both sites so they remain searchable and DOI-matchable; only the surrounding UI text and the profile are translated. The Chinese site points its PDF links at the same repo's `papers/` folder via `PDF_BASE`, so the 211 MB library is stored only once.
3. `deploy_api.py` now finds the token automatically (`GITHUB_TOKEN` → first CLI arg → Git Credential Manager), so no PAT needs to be pasted into the chat.

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

`git fetch/push` can stall behind proxies when uploading large binary files. The API deployer uploads blobs directly and creates one commit — 134 files / 211.8 MB in about two minutes:

```bash
python deploy_api.py                    # uses the credential saved by Git Credential Manager
GITHUB_TOKEN=ghp_xxx python deploy_api.py   # or pass one explicitly
```

It uses `base_tree` so remote-only files are preserved, and caches uploaded blob SHAs so an interrupted run can be resumed. Needs a repo-scoped PAT or a fine-grained token with **Contents: read + write** on `scumicrowave/homepage`. The token is never written to disk or printed.

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

> **Why GitHub Pages:** the free Tencent/WorkBuddy one-click host (CloudStudio sandbox) has
> **no custom-domain option** — `domainPrefix` only requests a friendlier first segment when an
> app is first created, re-publishing keeps the same link, and that sharecode URL cannot be
> indexed by Google. Tencent **EdgeOne Pages** does support custom domains but requires a
> Tencent Cloud account and an **ICP-filed (备案) domain**. GitHub Pages is free, needs no
> ICP filing, and now serves both languages from one repo.

The cheapest permanent route is the GitHub Pages repo you already have
(`scumicrowave/homepage`): custom domains are free, stable and need no ICP filing. Bind one
domain and both language editions get friendly URLs:

| Site | URL after binding |
|---|---|
| English | `https://<domain>/` |
| Chinese | `https://<domain>/zh/` |
| PDF files | `https://<domain>/papers/...` (or keep the `github.io` absolute links) |

Steps:

1. Own a domain you control DNS for. **`mwpt.tech` is expired / does not resolve** — do not use
   it until it is renewed and its DNS is under your control. A fresh domain or a subdomain of
   one you own is fine.
2. Add DNS records at your registrar (exact GitHub Pages values):
   - apex `@` → `A` `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - apex `@` → `AAAA` `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - `www` → `CNAME` `scumicrowave.github.io` — **never** include `/homepage` or the repo name
   - DNS may take up to 24 h; remove any default/wildcard records first.
3. In the repo, add a one-line `CNAME` file containing the chosen domain at the **root**, or let
   GitHub create it when you enter the domain under **Settings → Pages → Custom domain → Save**.
   Then enable **Enforce HTTPS**.
4. `python bind_domain.py <domain> --apply` does the local work for you: writes `CNAME`,
   updates `profile.site_url` / `profile_zh.site_url_zh`, rebuilds both editions and
   regenerates `robots.txt` + `sitemap.xml` with the new canonical URLs. Keep `zh/` in the repo
   so the Chinese site stays at `/zh/`. The Chinese page's PDF links remain on the stable
   `github.io` absolute URL, which keeps working through GitHub's redirect.
5. Push with `python deploy_api.py`, then re-submit the new sitemap URL in Search Console.

### Current decision: no custom domain yet

`mwpt.tech` (the old Chinese MWPT group site) **no longer resolves and appears expired**.
Writing a `CNAME` for a domain you do not control makes GitHub Pages serve 404s and creates a
takeover risk if the name is re-registered by someone else — so **`CNAME` is deliberately
absent** from the repo. Both language editions already work on the free, stable `github.io`
URLs listed at the top of this file, and both are indexed from there.

`bind_domain.py` is ready and now also regenerates `robots.txt` / `sitemap.xml`, so binding a
future domain is one command:

```bash
python bind_domain.py your-domain.com            # preview
python bind_domain.py your-domain.com --apply   # CNAME + site_url + rebuild + SEO
python deploy_api.py                            # push
```

GitHub write authorization is **no longer a blocker** — `deploy_api.py` reuses the credential
in Git Credential Manager. The only remaining external step is adding the DNS records at the
registrar, which requires the domain owner's login.

## Google Search / SEO

Both editions are set up for indexing. Everything that can be done from this workspace is done:

| Signal | Where |
|---|---|
| `robots.txt` (`Allow: /` + Sitemap directive) | `https://scumicrowave.github.io/homepage/robots.txt` |
| `sitemap.xml` (2 HTML pages + 116 PDFs, hreflang annotations) | `https://scumicrowave.github.io/homepage/sitemap.xml` |
| `rel=canonical` | English → `/homepage/`, Chinese → `/homepage/zh/` |
| `hreflang=en` / `zh-Hans` / `x-default` | In both pages **and** in the sitemap |
| schema.org `Person` JSON-LD with `url`, `inLanguage`, `alternateName` | Both pages |
| `og:locale`, `description`, visible cross-language links | Both pages |

**Note on project sites:** this is a project page (`scumicrowave.github.io/homepage/`), so
`robots.txt` lives under `/homepage/`, not at the host root (`scumicrowave.github.io/robots.txt`,
which returns 404). That root file belongs to the account-level `<username>.github.io` repo and
cannot be controlled from this repository. A 404 robots.txt means "no restrictions", so crawling
is unaffected. Submitting the sitemap directly in Search Console is the reliable path — and once
a custom domain is bound, `robots.txt` sits at the real root and the `Sitemap:` directive is
picked up automatically.

### Ownership verification — DONE ✅

Search Console asked for the HTML verification file to be uploaded to
`https://scumicrowave.github.io/homepage/`. It is committed at the repo root and live:

| | |
|---|---|
| File | `google89b0777337e2a7d8.html` |
| Live URL | `https://scumicrowave.github.io/homepage/google89b0777337e2a7d8.html` |
| Content | `google-site-verification: google89b0777337e2a7d8.html` |
| Checked | HTTP 200, `text/html`, 53 bytes, exact match |

> **Keep this file permanently.** Search Console says: *"To stay verified, don't remove the
> file, even after verification succeeds."* Google re-checks it periodically. `deploy_api.py`
> therefore treats `google*.html` as protected — it auto-detects missing verification files
> from the repo, refuses to deploy without them, and re-uploads them on every run. Do not
> delete or rename it, and do not add it to `.gitignore`.

A URL-prefix property (`https://scumicrowave.github.io/homepage/`) expects the file at the
**root of that prefix**, not at the host root — so this works on a project page. (The host root
`https://scumicrowave.github.io/googleXXXX.html` would belong to a separate
`<username>.github.io` account repo, which does not exist here.) The DNS TXT method would need
a Domain property with an apex domain you control; `mwpt.tech` is expired, so it only becomes
an option after `bind_domain.py --apply`. As a belt-and-braces fallback, `build.py` also
supports the HTML-tag method: put `"google_site_verification": "<content>"` in
`publications.json`, rebuild, and the meta tag is injected into both pages.

### Remaining steps — need your Google account

These are the only steps that cannot be done from this workspace (they require being logged in
to your Google account):

1. In https://search.google.com/search-console, open the **URL-prefix property**
   `https://scumicrowave.github.io/homepage/` and click **Verify** on the HTML-file method.
   The file is already live, so verification should succeed immediately.
2. **Sitemaps → Add** `https://scumicrowave.github.io/homepage/sitemap.xml` → **Submit**.
3. Optionally **URL Inspection → Request Indexing** for the two homepage URLs
   (quota is limited; the sitemap covers the other 116 PDF URLs).
4. Inspect `/homepage/zh/` too, and confirm the hreflang cluster is recognised under
   **International Targeting**.

Google's sitemap "ping" endpoint has been retired and the Indexing API only accepts
`JobPosting` / `BroadcastEvent` types, so Search Console is the only supported submission route.

## Content sources

Profile and publication list compiled from the existing Google Sites homepage, IEEE Xplore author profile, IEEE MTT-S profile, Sichuan University EIE faculty page and Baidu Baike. Google Scholar blocked automated retrieval, so citation counts come from IEEE Xplore (138 publications / 2,043 citations). The 116 PDFs come from the exported Google Drive folder `Public research articles` supplied as a local zip.

### Known data issues / to confirm

- The source Google Sites page assigned the **same Google Drive placeholder link** to many 2024 entries and reused one link across two 2021 papers. Those were dropped rather than published as broken downloads.
- Google Scholar ID confirmed as **`_6js4T4AAAAJ`**; the `vTWbtXkAAAAJ` ID on the old homepage is stale. `profile.links` already uses the confirmed one.
- The publication list covers 2015–2025 (no 2016 entries on the source page); IEEE Xplore shows work up to 2026 — add newer papers.
- The PDF library contains 116 files (~211 MB); every file is under 18 MB, within GitHub's 100 MB per-file limit and 1 GB soft repo limit.
- **Verify every hosted PDF is legally shareable** (publisher copyright / open-access / accepted-manuscript status) before making the repository public.
- The 2026-11-13 deployments used a one-off PAT first and then the credential stored in Git Credential Manager. **Revoke the one-off PAT** if it is still active; future updates just run `python deploy_api.py`.
