#!/usr/bin/env python3
"""Regenerate the academic homepage from publications.json.

Usage:
    python build.py            # English -> index.html
    python build.py --lang zh  # Chinese -> zh/index.html (+ self-contained assets)

publications.json is the single source of truth. `profile` holds the English
wording, `profile_zh` the Chinese wording. Publication titles, authors and
venues stay in English on both sites so they remain searchable / DOI-matchable.
Only the Python standard library is required.
"""

import html
import json
import shutil
import sys
import urllib.parse
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
PROFILE = DATA["profile"]
PAPERS = DATA["publications"]
DRIVE = PROFILE["drive_folder"]
PDF_BASE = "https://scumicrowave.github.io/homepage/"
# Canonical origin for SEO. bind_domain.py rewrites profile.site_url, so canonical tags,
# hreflang alternates, og:url and sitemap.xml all follow a future custom domain.
SITE_URL = PROFILE["site_url"].rstrip("/") + "/"
EN_URL = SITE_URL
ZH_URL = SITE_URL + "zh/"

LANG = "en"
if "--lang" in sys.argv:
    i = sys.argv.index("--lang")
    if i + 1 < len(sys.argv) and sys.argv[i + 1] == "zh":
        LANG = "zh"
elif "--lang=zh" in sys.argv:
    LANG = "zh"

P = DATA.get("profile_zh", {}) if LANG == "zh" else PROFILE
OUT = ROOT / "zh" if LANG == "zh" else ROOT

I18N = {
    "en": {
        "lang": "en",
        "page_title": "{name} \u2014 {title}, Sichuan University",
        "meta_desc": "{name}, {title} at {affiliation}. Research on microwave wireless power transmission, rectifiers and rectennas. Publications with PDF downloads.",
        "og_title": "{name} \u2014 Academic Homepage",
        "og_desc": "Microwave wireless power transmission, rectifiers and rectennas. Full publication list with PDF downloads.",
        "skip": "Skip to publications",
        "nav": ["About", "Research", "Publications", "PDF Repository", "Service", "Contact"],
        "side_contact": "Contact",
        "side_profiles": "Profiles",
        "lbl_email": "Email", "lbl_alt": "Alt.", "lbl_tel": "Tel", "lbl_orcid": "ORCID",
        "drive_btn": "Download all papers (PDF repository)",
        "h_about": "About", "h_research": "Research Interests", "h_pubs": "Publications",
        "h_repo": "PDF Repository", "h_service": "Professional Service",
        "h_honors": "Honors & Awards", "h_books": "Books", "h_contact": "Contact",
        "meta_pubs": "{total} entries &middot; {n_years} years &middot; {ymin}&ndash;{ymax} &middot; {n_pdf} with PDF links &middot; {n_local} hosted here",
        "intro_pubs": "Papers are listed in reverse chronological order. <strong>{name}</strong> is marked in the author list as <em>C. Liu</em> / <em>Changjun Liu</em>. Click <span class=\"inline-btn\">PDF</span> to download, or use the filters below.",
        "sr_search_pubs": "Search publications",
        "search_pubs": "Search title, author, venue&hellip;",
        "chip_all": "All", "chip_all_types": "All types",
        "types": {"journal": "Journal", "conference": "Conference", "magazine": "Magazine",
                  "patent": "Patent", "editorial": "Editorial", "book": "Book"},
        "empty_pubs": "No publications match the current filters.",
        "footnote_pubs": "\u2020 No direct PDF link is available for this entry yet. The button opens the public paper repository where the full text can be downloaded. Starred entries (\u2605) are selected publications.",
        "meta_repo": "{n} full texts hosted on this site",
        "intro_repo": "Every full text in the <code>papers/</code> folder is hosted directly on this site, so downloads do not depend on Google Drive or publisher links. Grouped by publication year where the year is confirmed; files without a confirmed year are listed at the end. Click <span class=\"inline-btn\">PDF</span> to download, or search the repository below.",
        "sr_search_repo": "Search the PDF repository",
        "search_repo": "Search PDF titles&hellip;",
        "empty_repo": "No PDFs match the current search.",
        "footnote_repo": "PDFs are served as-is. Please observe publisher copyright and open-access terms before redistributing them.",
        "undated": "Earlier works & undated full texts",
        "btn_mirror": "Mirror", "btn_doi": "DOI", "btn_scholar": "Scholar",
        "btn_pdf_fallback": "PDF \u2020",
        "tip_local": "PDF hosted on this site (GitHub Pages)",
        "tip_pdf": "Download PDF",
        "tip_fallback": "Opens the public paper repository",
        "star_tip": "Selected publication",
        "contact_note": "Prospective students interested in microwave wireless power transmission, rectifiers, or rectennas are welcome to get in touch.",
        "footer_updated": "Last updated",
        "footer_built": "Built as a static site for GitHub Pages.",
        "alt_version": "中文版 / Chinese",
    },
    "zh": {
        "lang": "zh-CN",
        "page_title": "{name} \u2014 {title}，四川大学",
        "meta_desc": "{name}，{affiliation}{title}。研究方向为微波与毫米波无线电能传输、高效率整流器与整流天线。按年份列出发表论文并提供 PDF 下载。",
        "og_title": "{name} \u2014 中文学术主页",
        "og_desc": "微波无线电能传输、整流器与整流天线；按年份列出全部论文并提供 PDF 下载。",
        "skip": "跳转到论文列表",
        "nav": ["简介", "研究方向", "发表论文", "PDF 文库", "学术服务", "联系方式"],
        "side_contact": "联系方式",
        "side_profiles": "学术档案",
        "lbl_email": "邮箱", "lbl_alt": "备用邮箱", "lbl_tel": "电话", "lbl_orcid": "ORCID",
        "drive_btn": "下载全部论文（PDF 文库）",
        "h_about": "个人简介", "h_research": "研究方向", "h_pubs": "发表论文",
        "h_repo": "PDF 文库", "h_service": "学术兼职",
        "h_honors": "荣誉与奖励", "h_books": "著作", "h_contact": "联系方式",
        "meta_pubs": "{total} 条 &middot; {n_years} 个年份 &middot; {ymin}&ndash;{ymax} &middot; {n_pdf} 条含 PDF 链接 &middot; {n_local} 条可直接下载",
        "intro_pubs": "论文按发表年份倒序排列。<strong>{name}</strong> 在作者列表中标注为 <em>C. Liu</em> / <em>Changjun Liu</em>。点击 <span class=\"inline-btn\">PDF</span> 下载，或使用下方筛选。论文标题、作者及期刊信息保留英文原文，便于检索与 DOI 核对。",
        "sr_search_pubs": "搜索论文",
        "search_pubs": "搜索标题、作者、期刊…",
        "chip_all": "全部", "chip_all_types": "全部类型",
        "types": {"journal": "期刊", "conference": "会议", "magazine": "杂志",
                  "patent": "专利", "editorial": "社论", "book": "专著"},
        "empty_pubs": "没有符合条件的论文。",
        "footnote_pubs": "\u2020 该条目暂无直接 PDF 链接，按钮将打开公共论文库以下载全文。带星号（\u2605）的为代表性论文。",
        "meta_repo": "{n} 篇全文 PDF 可供下载",
        "intro_repo": "全部全文 PDF 托管于本站配套的英文站点文件库，点击 <span class=\"inline-btn\">PDF</span> 即可下载，无需跳转 Google Drive 或出版社页面。按已确认的发表年份分组；年份未确认的文件列于末尾。也可在下方搜索文库。",
        "sr_search_repo": "搜索 PDF 文库",
        "search_repo": "搜索 PDF 标题…",
        "empty_repo": "没有符合条件的 PDF。",
        "footnote_repo": "PDF 按原文件提供。再次分发时请遵守出版社版权与开放获取条款。",
        "undated": "早期论文及年份未确认的全文",
        "btn_mirror": "镜像", "btn_doi": "DOI", "btn_scholar": "学术搜索",
        "btn_pdf_fallback": "PDF \u2020",
        "tip_local": "PDF 由本站文件库提供",
        "tip_pdf": "下载 PDF",
        "tip_fallback": "打开公共论文库",
        "star_tip": "代表性论文",
        "contact_note": "欢迎对微波无线电能传输、整流器或整流天线感兴趣的同学联系。",
        "footer_updated": "最后更新",
        "footer_built": "静态站点 · GitHub Pages",
        "alt_version": "English version",
    },
}
T = I18N[LANG]


def esc(value):
    return html.escape(str(value), quote=True)


def scholar_url(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote_plus(title)


def local_url(path):
    """Chinese site has no PDF copies: point at the published English site."""
    u = urllib.parse.quote(path, safe="/")
    return PDF_BASE + u if LANG == "zh" else u


def pdf_target(paper):
    """Return (url, label, tooltip) for the primary PDF button."""
    if paper.get("local"):
        return local_url(paper["local"]), "PDF", T["tip_local"]
    if paper.get("pdf"):
        return paper["pdf"], "PDF", T["tip_pdf"]
    return DRIVE, T["btn_pdf_fallback"], T["tip_fallback"]


def render_paper(paper, index):
    title = paper["title"]
    authors = paper["authors"]
    venue = paper["venue"]
    ptype = paper.get("type", "journal")
    ptype_label = T["types"].get(ptype, ptype.title())
    pdf_url, pdf_label, pdf_tip = pdf_target(paper)
    search_blob = " ".join([title, authors, venue, ptype_label, str(paper["year"])]).lower()

    links = [
        f'<a class="btn btn-pdf" href="{esc(pdf_url)}" title="{esc(pdf_tip)}" '
        f'target="_blank" rel="noopener">{esc(pdf_label)}</a>'
    ]
    if paper.get("local") and paper.get("pdf"):
        links.append(
            f'<a class="btn btn-ghost" href="{esc(paper["pdf"])}" '
            f'target="_blank" rel="noopener">{esc(T["btn_mirror"])}</a>'
        )
    if paper.get("doi"):
        links.append(
            f'<a class="btn btn-ghost" href="{esc("https://doi.org/" + paper["doi"])}" '
            f'target="_blank" rel="noopener">{esc(T["btn_doi"])}</a>'
        )
    links.append(
        f'<a class="btn btn-ghost" href="{esc(scholar_url(title))}" '
        f'target="_blank" rel="noopener">{esc(T["btn_scholar"])}</a>'
    )

    star = (
        f'<span class="star" title="{esc(T["star_tip"])}" aria-label="{esc(T["star_tip"])}">'
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
        for n, label in P["stats"]
    )


def render_links():
    return "\n".join(
        f'        <li><a href="{esc(url)}" target="_blank" rel="noopener">{esc(name)}'
        f'<span aria-hidden="true">\u2197</span></a></li>'
        for name, url in P["links"]
    )


def render_bio():
    return "\n".join(f"        <p>{esc(p)}</p>" for p in P["bio"])


def render_avatar():
    photo = ROOT / "assets" / "photo.jpg"
    if photo.exists():
        return f'<img class="avatar" src="assets/photo.jpg" alt="{esc(P["name"])}">'
    initials = P["name"][:2] if LANG == "zh" else "".join(w[0] for w in PROFILE["name"].split()[:2]).upper()
    return f'<div class="avatar avatar-mono" role="img" aria-label="{esc(P["name"])}">{esc(initials)}</div>'


def canonical_url():
    return ZH_URL if LANG == "zh" else EN_URL


def render_seo():
    """Canonical + hreflang + Open Graph signals for both language editions."""
    canonical = canonical_url()
    own_locale = "zh_CN" if LANG == "zh" else "en_US"
    other_locale = "en_US" if LANG == "zh" else "zh_CN"
    lines = [
        f'  <link rel="canonical" href="{esc(canonical)}">',
        f'  <link rel="alternate" hreflang="en" href="{esc(EN_URL)}">',
        f'  <link rel="alternate" hreflang="zh-Hans" href="{esc(ZH_URL)}">',
        f'  <link rel="alternate" hreflang="x-default" href="{esc(EN_URL)}">',
        '  <meta name="robots" content="index, follow, max-image-preview:large">',
        f'  <meta property="og:site_name" content="{esc(P["name"])} | Sichuan University">',
        f'  <meta property="og:url" content="{esc(canonical)}">',
        f'  <meta property="og:locale" content="{own_locale}">',
        f'  <meta property="og:locale:alternate" content="{other_locale}">',
    ]
    ver = DATA.get("google_site_verification")
    if ver:
        lines.append(f'  <meta name="google-site-verification" content="{esc(ver)}">')
    return "\n".join(lines)


def render_jsonld():
    schema = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": P["name"],
        "jobTitle": P["title"],
        "affiliation": {
            "@type": "CollegeOrUniversity",
            "name": P["affiliation"],
        },
        "email": PROFILE["email"],
        "address": P["location"],
        "identifier": "https://orcid.org/" + PROFILE["orcid"],
        "sameAs": [url for _, url in P["links"]],
        "url": canonical_url(),
        "inLanguage": T["lang"],
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url()},
    }
    if LANG == "zh":
        schema["alternateName"] = PROFILE["name"]
    return json.dumps(schema, ensure_ascii=False, indent=2)


def render_yearchips():
    years = sorted({p["year"] for p in PAPERS}, reverse=True)
    chips = [f'<button class="chip is-active" data-year="all">{esc(T["chip_all"])}</button>']
    chips += [f'<button class="chip" data-year="{y}">{y}</button>' for y in years]
    return "\n          ".join(chips)


def render_pdf_library():
    """Render every PDF as a downloadable, searchable list, grouped by year.

    Only years confirmed from a publication record or a dated filename are used.
    PDF file creation dates are deliberately NOT treated as publication years.
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
        label = str(year) if year else T["undated"]
        rows = []
        for it in group:
            n += 1
            url = local_url(it["file"])
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

    page_title = T["page_title"].format(name=P["name"], title=P["title"], affiliation=P["affiliation"])
    meta_desc = T["meta_desc"].format(name=P["name"], title=P["title"], affiliation=P["affiliation"])
    og_title = T["og_title"].format(name=P["name"])
    meta_pubs = T["meta_pubs"].format(total=total, n_years=n_years, ymin=year_min,
                                      ymax=year_max, n_pdf=n_pdf, n_local=n_local)
    intro_pubs = T["intro_pubs"].format(name=esc(P["name"]))
    meta_repo = T["meta_repo"].format(n=n_lib)
    alt_target = ZH_URL if LANG == "en" else EN_URL
    alt_hreflang = "zh-Hans" if LANG == "en" else "en"
    alt_link = (
        f'    <p class="aff-sub"><a href="{esc(alt_target)}" hreflang="{alt_hreflang}">'
        f'{esc(T["alt_version"])} \u2197</a></p>'
        if T["alt_version"] else ""
    )
    nav = "\n      ".join(
        f'<a href="#{anchor}">{esc(label)}</a>'
        for anchor, label in zip(["about", "research", "publications", "repository", "service", "contact"], T["nav"])
    )

    doc = f'''<!doctype html>
<html lang="{T["lang"]}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title)}</title>
  <meta name="description" content="{esc(meta_desc)}">
  <meta name="author" content="{esc(P["name"])}">
{render_seo()}
  <meta property="og:type" content="profile">
  <meta property="og:title" content="{esc(og_title)}">
  <meta property="og:description" content="{esc(T["og_desc"])}">
  <link rel="stylesheet" href="assets/style.css">
  <script type="application/ld+json">
{render_jsonld()}
  </script>
</head>
<body>
<a class="skip-link" href="#publications">{esc(T["skip"])}</a>

<header class="topbar">
  <div class="wrap topbar-inner">
    <a class="brand" href="#about">{esc(P["name"])} <span>{esc(PROFILE["name"] if LANG == "zh" else PROFILE["name_zh"])}</span></a>
    <nav class="topnav" aria-label="{esc(T["side_profiles"])}">
      {nav}
    </nav>
  </div>
</header>

<div class="wrap layout">
  <aside class="sidebar">
{render_avatar()}
    <h1 class="name">{esc(P["name"])}</h1>
    <p class="role">{esc(P["title"])}</p>
    <p class="aff">{esc(P["affiliation"])}<br>{esc(P["location"])}</p>
    <p class="aff-sub">{esc(P["extra_role"])}</p>

    <h2 class="side-title">{esc(T["side_contact"])}</h2>
    <ul class="contact">
      <li><span>{esc(T["lbl_email"])}</span><a href="mailto:{esc(PROFILE["email"])}">{esc(PROFILE["email"])}</a></li>
      <li><span>{esc(T["lbl_alt"])}</span><a href="mailto:{esc(PROFILE["email_alt"])}">{esc(PROFILE["email_alt"])}</a></li>
      <li><span>{esc(T["lbl_tel"])}</span><a href="tel:{esc(PROFILE["phone"].replace(' ', ''))}">{esc(PROFILE["phone"])}</a></li>
      <li><span>{esc(T["lbl_orcid"])}</span><a href="https://orcid.org/{esc(PROFILE["orcid"])}" target="_blank" rel="noopener">{esc(PROFILE["orcid"])}</a></li>
    </ul>

    <h2 class="side-title">{esc(T["side_profiles"])}</h2>
    <ul class="links">
{render_links()}
    </ul>

    <a class="drive-btn" href="{esc(DRIVE)}" target="_blank" rel="noopener">{esc(T["drive_btn"])} <span aria-hidden="true">\u2197</span></a>
{alt_link}
  </aside>

  <main class="content">
    <section id="about" class="card">
      <h2>{esc(T["h_about"])}</h2>
{render_bio()}
      <div class="stats">
{render_stats()}
      </div>
    </section>

    <section id="research" class="card">
      <h2>{esc(T["h_research"])}</h2>
      <ul class="interest-list">
{render_list(P["interests"])}
      </ul>
    </section>

    <section id="publications" class="card">
      <div class="section-head">
        <h2>{esc(T["h_pubs"])}</h2>
        <span class="section-meta">{meta_pubs}</span>
      </div>
      <p class="intro">{intro_pubs}</p>

      <div class="toolbar">
        <label class="search-wrap">
          <span class="sr-only">{esc(T["sr_search_pubs"])}</span>
          <input id="q" type="search" placeholder="{esc(T["search_pubs"])}" autocomplete="off">
        </label>
        <div class="chips" id="year-chips" role="group" aria-label="{esc(T["chip_all"])}">
          {render_yearchips()}
        </div>
        <div class="chips chips-type" id="type-chips" role="group" aria-label="{esc(T["chip_all_types"])}">
          <button class="chip is-active" data-type="all">{esc(T["chip_all_types"])}</button>
          <button class="chip" data-type="journal">{esc(T["types"]["journal"])}</button>
          <button class="chip" data-type="conference">{esc(T["types"]["conference"])}</button>
          <button class="chip" data-type="magazine">{esc(T["types"]["magazine"])}</button>
          <button class="chip" data-type="patent">{esc(T["types"]["patent"])}</button>
          <button class="chip" data-type="editorial">{esc(T["types"]["editorial"])}</button>
        </div>
        <p class="result-count" id="result-count" aria-live="polite"></p>
      </div>

      <div id="publist">
{years_html}
      </div>
      <p class="empty-state" id="empty-state" hidden>{esc(T["empty_pubs"])}</p>
      <p class="footnote">{esc(T["footnote_pubs"])}</p>
    </section>

    <section id="repository" class="card">
      <div class="section-head">
        <h2>{esc(T["h_repo"])}</h2>
        <span class="section-meta">{esc(meta_repo)}</span>
      </div>
      <p class="intro">{T["intro_repo"]}</p>
      <div class="lib-toolbar">
        <label class="search-wrap">
          <span class="sr-only">{esc(T["sr_search_repo"])}</span>
          <input id="lib-q" type="search" placeholder="{esc(T["search_repo"])}" autocomplete="off">
        </label>
        <p class="result-count" id="lib-count" aria-live="polite"></p>
      </div>
      <div class="pdf-library">
{render_pdf_library()}
      </div>
      <p class="library-empty" id="library-empty" hidden>{esc(T["empty_repo"])}</p>
      <p class="footnote">{esc(T["footnote_repo"])}</p>
    </section>

    <section id="service" class="card two-col">
      <div>
        <h2>{esc(T["h_service"])}</h2>
        <ul class="plain-list">
{render_list(P["service"])}
        </ul>
      </div>
      <div>
        <h2>{esc(T["h_honors"])}</h2>
        <ul class="plain-list">
{render_list(P["honors"])}
        </ul>
      </div>
    </section>

    <section id="books" class="card">
      <h2>{esc(T["h_books"])}</h2>
      <ul class="plain-list">
{render_list(P["books"])}
      </ul>
    </section>

    <section id="contact" class="card">
      <h2>{esc(T["h_contact"])}</h2>
      <p>{esc(P["affiliation"])}<br>{esc(P["location"])}</p>
      <p>{esc(T["lbl_email"])}: <a href="mailto:{esc(PROFILE["email"])}">{esc(PROFILE["email"])}</a> &middot; {esc(T["lbl_tel"])}: {esc(PROFILE["phone"])}</p>
      <p class="muted">{esc(T["contact_note"])}</p>
    </section>
  </main>
</div>

<footer class="footer">
  <div class="wrap">
    <span>&copy; {esc(P["name"])} &middot; {esc(T["footer_updated"])} {esc(__import__('datetime').date.today().isoformat())}</span>
    <span>{esc(T["footer_built"])}</span>
  </div>
</footer>

<script src="assets/app.js"></script>
</body>
</html>
'''
    OUT.mkdir(parents=True, exist_ok=True)
    if LANG == "zh":
        (OUT / "assets").mkdir(exist_ok=True)
        for name in ("style.css", "app.js"):
            shutil.copy2(ROOT / "assets" / name, OUT / "assets" / name)
    (OUT / "index.html").write_text(doc, encoding="utf-8")
    print(f"Wrote {OUT / 'index.html'}: {LANG}, {total} publications, {n_years} year groups, "
          f"{n_local} self-hosted PDF links, {n_lib} files in the PDF repository.")


if __name__ == "__main__":
    main()
