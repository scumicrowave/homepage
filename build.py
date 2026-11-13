#!/usr/bin/env python3
"""Regenerate index.html from publications.json.

Usage:
    python build.py

Edit publications.json (single source of truth), run this script, then commit
the regenerated index.html. No dependencies beyond the Python standard library.
"""

import html
import json
import urllib.parse
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
PROFILE = DATA["profile"]
PAPERS = DATA["publications"]
DRIVE = PROFILE["drive_folder"]

TYPE_LABELS = {
    "journal": "Journal",
    "conference": "Conference",
    "magazine": "Magazine",
    "patent": "Patent",
    "editorial": "Editorial",
    "book": "Book",
}


def esc(value):
    return html.escape(str(value), quote=True)


def scholar_url(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote_plus(title)


def pdf_target(paper):
    """Return (url, label, tooltip) for the primary PDF button."""
    if paper.get("local"):
        # Percent-encode spaces / unicode in filenames, keep path separators.
        return urllib.parse.quote(paper["local"], safe="/"), "PDF", "PDF hosted on this site (GitHub Pages)"
    if paper.get("pdf"):
        return paper["pdf"], "PDF", "Download PDF"
    return DRIVE, "PDF \u2020", "Opens the public paper repository"


def render_paper(paper, index):
    title = paper["title"]
    authors = paper["authors"]
    venue = paper["venue"]
    ptype = paper.get("type", "journal")
    ptype_label = TYPE_LABELS.get(ptype, ptype.title())
    pdf_url, pdf_label, pdf_tip = pdf_target(paper)
    search_blob = " ".join([title, authors, venue, ptype_label, str(paper["year"])]).lower()

    links = [
        f'<a class="btn btn-pdf" href="{esc(pdf_url)}" title="{esc(pdf_tip)}" '
        f'target="_blank" rel="noopener">{esc(pdf_label)}</a>'
    ]
    if paper.get("local") and paper.get("pdf"):
        links.append(
            f'<a class="btn btn-ghost" href="{esc(paper["pdf"])}" '
            f'target="_blank" rel="noopener">Mirror</a>'
        )
    if paper.get("doi"):
        links.append(
            f'<a class="btn btn-ghost" href="{esc("https://doi.org/" + paper["doi"])}" '
            f'target="_blank" rel="noopener">DOI</a>'
        )
    links.append(
        f'<a class="btn btn-ghost" href="{esc(scholar_url(title))}" '
        f'target="_blank" rel="noopener">Scholar</a>'
    )

    star = (
        '<span class="star" title="Selected publication" aria-label="Selected publication">'
        "\u2605</span> "
        if paper.get("selected")
        else ""
    )

    return f'''      <li class="paper" data-year="{paper['year']}" data-type="{esc(ptype)}" data-text="{esc(search_blob)}">
        <div class="paper-head"><span class="idx">{index:02d}</span><span class="badge">{esc(ptype_label)}</span></div>
        <div class="paper-title">{star}{esc(title)}</div>
        <div class="paper-authors">{esc(authors)}</div>
        <div class="paper-venue">{esc(venue)}</div>
        <div class="paper-actions">{''.join(links)}</div>
      </li>'''


def render_years():
    grouped = OrderedDict()
    for p in PAPERS:
        grouped.setdefault(p["year"], []).append(p)

    out = []
    counter = 1
    for year, items in grouped.items():
        rows = "\n".join(render_paper(p, counter + i) for i, p in enumerate(items))
        counter += len(items)
        out.append(f'''    <section class="year-group" data-year="{year}">
      <h3 class="year-heading">{year}<span class="year-count">{len(items)}</span></h3>
      <ol class="papers" start="{counter - len(items)}">
{rows}
      </ol>
    </section>''')
    return "\n".join(out), len(grouped)


def render_list(items, tag="li"):
    return "\n".join(f"        <{tag}>{esc(x)}</{tag}>" for x in items)


def render_stats():
    return "\n".join(
        f'        <div class="stat"><strong>{esc(n)}</strong><span>{esc(label)}</span></div>'
        for n, label in PROFILE["stats"]
    )


def render_links():
    return "\n".join(
        f'        <li><a href="{esc(url)}" target="_blank" rel="noopener">{esc(name)}'
        f'<span aria-hidden="true">\u2197</span></a></li>'
        for name, url in PROFILE["links"]
    )


def render_bio():
    return "\n".join(f"        <p>{esc(p)}</p>" for p in PROFILE["bio"])


def render_avatar():
    photo = ROOT / "assets" / "photo.jpg"
    if photo.exists():
        return f'<img class="avatar" src="assets/photo.jpg" alt="{esc(PROFILE["name"])}">'
    initials = "".join(w[0] for w in PROFILE["name"].split()[:2]).upper()
    return f'<div class="avatar avatar-mono" role="img" aria-label="Portrait placeholder">{esc(initials)}</div>'


def render_jsonld():
    schema = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": PROFILE["name"],
        "jobTitle": PROFILE["title"],
        "affiliation": {
            "@type": "CollegeOrUniversity",
            "name": PROFILE["affiliation"],
        },
        "email": PROFILE["email"],
        "address": PROFILE["location"],
        "url": PROFILE["site_url"],
        "identifier": "https://orcid.org/" + PROFILE["orcid"],
        "sameAs": [url for _, url in PROFILE["links"]],
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def render_yearchips():
    years = sorted({p["year"] for p in PAPERS}, reverse=True)
    chips = ['<button class="chip is-active" data-year="all">All</button>']
    chips += [f'<button class="chip" data-year="{y}">{y}</button>' for y in years]
    return "\n          ".join(chips)


def render_pdf_library():
    """Render every PDF in papers/ as a downloadable, searchable list.

    Only years confirmed from a publication record or a dated filename are used
    for grouping. PDF file creation dates are deliberately NOT treated as
    publication years, so unconfirmed files are collected in a final group.
    """
    items = DATA.get("full_pdf_library", [])
    grouped = OrderedDict()
    for it in items:
        grouped.setdefault(it.get("year"), []).append(it)

    out = []
    n = 0
    years = sorted([y for y in grouped if y], reverse=True)
    for year in years + [None]:
        group = grouped.get(year, [])
        if not group:
            continue
        label = str(year) if year else "Earlier works & undated full texts"
        rows = []
        for it in group:
            n += 1
            url = urllib.parse.quote(it["file"], safe="/")
            blob = " ".join([it["title"], str(year or ""), it["file"]]).lower()
            rows.append(
                f'        <li class="lib-item" data-text="{esc(blob)}">'
                f'<span class="add-num">{n:03d}</span>'
                f'<span class="add-title">{esc(it["title"])}</span>'
                f'<a class="btn btn-pdf" href="{esc(url)}" target="_blank" rel="noopener">PDF</a></li>'
            )
        out.append(
            f'      <h4 class="lib-year" data-libyear="{esc(label)}">{esc(label)}'
            f'<span class="year-count">{len(group)}</span></h4>'
            f'      <ul class="additional-list" data-libgroup="{esc(label)}">\n'
            + "\n".join(rows) + "\n      </ul>"
        )
    return "\n".join(out)


def main():
    years_html, n_years = render_years()
    total = len(PAPERS)
    n_pdf = sum(1 for p in PAPERS if p.get("pdf") or p.get("local"))
    n_local = sum(1 for p in PAPERS if p.get("local"))
    n_lib = len(DATA.get("full_pdf_library", []))
    year_min = min(p["year"] for p in PAPERS)
    year_max = max(p["year"] for p in PAPERS)

    doc = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(PROFILE["name"])} &mdash; {esc(PROFILE["title"])}, Sichuan University</title>
  <meta name="description" content="{esc(PROFILE["name"])}, {esc(PROFILE["title"])} at {esc(PROFILE["affiliation"])}. Research on microwave wireless power transmission, rectifiers and rectennas. Publications with PDF downloads.">
  <meta name="author" content="{esc(PROFILE["name"])}">
  <meta property="og:type" content="profile">
  <meta property="og:title" content="{esc(PROFILE["name"])} &mdash; Academic Homepage">
  <meta property="og:description" content="Microwave wireless power transmission, rectifiers and rectennas. Full publication list with PDF downloads.">
  <link rel="stylesheet" href="assets/style.css">
  <script type="application/ld+json">
{render_jsonld()}
  </script>
</head>
<body>
<a class="skip-link" href="#publications">Skip to publications</a>

<header class="topbar">
  <div class="wrap topbar-inner">
    <a class="brand" href="#about">{esc(PROFILE["name"])} <span>{esc(PROFILE["name_zh"])}</span></a>
    <nav class="topnav" aria-label="Main navigation">
      <a href="#about">About</a>
      <a href="#research">Research</a>
      <a href="#publications">Publications</a>
      <a href="#repository">PDF Repository</a>
      <a href="#service">Service</a>
      <a href="#contact">Contact</a>
    </nav>
  </div>
</header>

<div class="wrap layout">
  <aside class="sidebar">
{render_avatar()}
    <h1 class="name">{esc(PROFILE["name"])}</h1>
    <p class="role">{esc(PROFILE["title"])}</p>
    <p class="aff">{esc(PROFILE["affiliation"])}<br>{esc(PROFILE["location"])}</p>
    <p class="aff-sub">{esc(PROFILE["extra_role"])}</p>

    <h2 class="side-title">Contact</h2>
    <ul class="contact">
      <li><span>Email</span><a href="mailto:{esc(PROFILE["email"])}">{esc(PROFILE["email"])}</a></li>
      <li><span>Alt.</span><a href="mailto:{esc(PROFILE["email_alt"])}">{esc(PROFILE["email_alt"])}</a></li>
      <li><span>Tel</span><a href="tel:{esc(PROFILE["phone"].replace(' ', ''))}">{esc(PROFILE["phone"])}</a></li>
      <li><span>ORCID</span><a href="https://orcid.org/{esc(PROFILE["orcid"])}" target="_blank" rel="noopener">{esc(PROFILE["orcid"])}</a></li>
    </ul>

    <h2 class="side-title">Profiles</h2>
    <ul class="links">
{render_links()}
    </ul>

    <a class="drive-btn" href="{esc(DRIVE)}" target="_blank" rel="noopener">Download all papers (PDF repository) <span aria-hidden="true">\u2197</span></a>
  </aside>

  <main class="content">
    <section id="about" class="card">
      <h2>About</h2>
{render_bio()}
      <div class="stats">
{render_stats()}
      </div>
    </section>

    <section id="research" class="card">
      <h2>Research Interests</h2>
      <ul class="interest-list">
{render_list(PROFILE["interests"])}
      </ul>
    </section>

    <section id="publications" class="card">
      <div class="section-head">
        <h2>Publications</h2>
        <span class="section-meta">{total} entries &middot; {n_years} years &middot; {year_min}&ndash;{year_max} &middot; {n_pdf} with PDF links &middot; {n_local} hosted here</span>
      </div>
      <p class="intro">Papers are listed in reverse chronological order. <strong>{esc(PROFILE["name"])}</strong> is marked in the author list as <em>C. Liu</em> / <em>Changjun Liu</em>. Click <span class="inline-btn">PDF</span> to download, or use the filters below.</p>

      <div class="toolbar">
        <label class="search-wrap">
          <span class="sr-only">Search publications</span>
          <input id="q" type="search" placeholder="Search title, author, venue&hellip;" autocomplete="off">
        </label>
        <div class="chips" id="year-chips" role="group" aria-label="Filter by year">
          {render_yearchips()}
        </div>
        <div class="chips chips-type" id="type-chips" role="group" aria-label="Filter by type">
          <button class="chip is-active" data-type="all">All types</button>
          <button class="chip" data-type="journal">Journal</button>
          <button class="chip" data-type="conference">Conference</button>
          <button class="chip" data-type="magazine">Magazine</button>
          <button class="chip" data-type="patent">Patent</button>
          <button class="chip" data-type="editorial">Editorial</button>
        </div>
        <p class="result-count" id="result-count" aria-live="polite"></p>
      </div>

      <div id="publist">
{years_html}
      </div>
      <p class="empty-state" id="empty-state" hidden>No publications match the current filters.</p>
      <p class="footnote">\u2020 No direct PDF link is available for this entry yet. The button opens the public paper repository where the full text can be downloaded. Starred entries (\u2605) are selected publications.</p>
    </section>

    <section id="repository" class="card">
      <div class="section-head">
        <h2>PDF Repository</h2>
        <span class="section-meta">{n_lib} full texts hosted on this site</span>
      </div>
      <p class="intro">Every full text in the <code>papers/</code> folder is hosted directly on this site, so downloads do not depend on Google Drive or publisher links. Grouped by publication year where the year is confirmed; files without a confirmed year are listed at the end. Click <span class="inline-btn">PDF</span> to download, or search the repository below.</p>
      <div class="lib-toolbar">
        <label class="search-wrap">
          <span class="sr-only">Search the PDF repository</span>
          <input id="lib-q" type="search" placeholder="Search PDF titles&hellip;" autocomplete="off">
        </label>
        <p class="result-count" id="lib-count" aria-live="polite"></p>
      </div>
      <div class="pdf-library">
{render_pdf_library()}
      </div>
      <p class="library-empty" id="library-empty" hidden>No PDFs match the current search.</p>
      <p class="footnote">PDFs are served as-is. Please observe publisher copyright and open-access terms before redistributing them.</p>
    </section>

    <section id="service" class="card two-col">
      <div>
        <h2>Professional Service</h2>
        <ul class="plain-list">
{render_list(PROFILE["service"])}
        </ul>
      </div>
      <div>
        <h2>Honors &amp; Awards</h2>
        <ul class="plain-list">
{render_list(PROFILE["honors"])}
        </ul>
      </div>
    </section>

    <section id="books" class="card">
      <h2>Books</h2>
      <ul class="plain-list">
{render_list(PROFILE["books"])}
      </ul>
    </section>

    <section id="contact" class="card">
      <h2>Contact</h2>
      <p>{esc(PROFILE["affiliation"])}<br>{esc(PROFILE["location"])}</p>
      <p>Email: <a href="mailto:{esc(PROFILE["email"])}">{esc(PROFILE["email"])}</a> &middot; Tel: {esc(PROFILE["phone"])}</p>
      <p class="muted">Prospective students interested in microwave wireless power transmission, rectifiers, or rectennas are welcome to get in touch.</p>
    </section>
  </main>
</div>

<footer class="footer">
  <div class="wrap">
    <span>&copy; {esc(PROFILE["name"])} &middot; Last updated {esc(__import__('datetime').date.today().isoformat())}</span>
    <span>Built as a static site for GitHub Pages.</span>
  </div>
</footer>

<script src="assets/app.js"></script>
</body>
</html>
'''
    (ROOT / "index.html").write_text(doc, encoding="utf-8")
    print(f"Wrote index.html: {total} publications, {n_years} year groups, "
          f"{n_local} self-hosted PDF links, {n_lib} files in the PDF repository.")


if __name__ == "__main__":
    main()
