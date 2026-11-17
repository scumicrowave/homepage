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
import re
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

# Circular portrait shown at the top-left of both language editions.
# build.py already falls back to initials if the file is not present.
PHOTO_NAME = "photo.jpg"
PHOTO_PATH = ROOT / "assets" / PHOTO_NAME
PHOTO_URL = SITE_URL + "assets/" + PHOTO_NAME

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
        "year_link_tip": "View all {year} papers and PDFs on a dedicated page",
        "sr_search_pubs": "Search publications",
        "search_pubs": "Search title, author, venue&hellip;",
        "chip_all": "All", "chip_all_types": "All types",
        "types": {"journal": "Journal", "conference": "Conference", "magazine": "Magazine",
                  "patent": "Patent", "editorial": "Editorial", "book": "Book",
                  "chapter": "Book Chapter"},
        "empty_pubs": "No publications match the current filters.",
        "footnote_pubs": "\u2020 No direct PDF link is available for this entry yet. The button opens the public paper repository where the full text can be downloaded. Starred entries (\u2605) are selected publications.",
        "meta_repo": "{n} full texts hosted on this site",
        "intro_repo": "All full texts are hosted directly on this site, so downloads do not depend on Google Drive or publisher links. Enter a paper title below to search and download the matching PDF &mdash; the list is hidden until you search.",
        "sr_search_repo": "Search the PDF repository",
        "search_repo": "Search PDF titles&hellip;",
        "empty_repo": "No PDFs match the current search.",
        "footnote_repo": "PDFs are served as-is. Please observe publisher copyright and open-access terms before redistributing them.",
        "repo_hint": "Enter a title above to search the full-text PDFs; matching files will appear here with a download link.",
        "undated": "Earlier works & undated full texts",
        "sec_conference": "Conference Papers",
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
        # Single-paper detail page
        "detail_back": "Back to publications",
        "detail_output": "Research output",
        "detail_output_journal": "Journal article",
        "detail_output_conf": "Conference paper",
        "detail_output_magazine": "Magazine article",
        "detail_output_other": "Publication",
        "detail_orig_lang": "Original language",
        "detail_lang_val": "English",
        "detail_lang_zh": "Chinese",
        "detail_pages": "Pages (from-to)",
        "detail_journal": "Journal",
        "detail_volume": "Volume",
        "detail_issue": "Issue number",
        "detail_pubdate": "Publication date",
        "detail_doi": "DOI",
        "detail_status": "Publication status",
        "detail_status_val": "Published",
        "detail_type_label": "Publication type",
        "detail_access": "Access to document",
        "detail_cite": "Cite this",
        "detail_cite_apa": "APA",
        "detail_cite_bibtex": "BibTeX",
        "detail_abstract_note": "Full text available via the download link below.",
        "detail_abstract": "Abstract",
        "detail_keywords": "Keywords",
        "detail_scholar": "View on Google Scholar",
        "detail_other": "Other links",
        "detail_title_tip": "View full publication details",
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
        "year_link_tip": "查看 {year} 年全部论文与 PDF（独立页面）",
        "sr_search_pubs": "搜索论文",
        "search_pubs": "搜索标题、作者、期刊…",
        "chip_all": "全部", "chip_all_types": "全部类型",
        "types": {"journal": "期刊", "conference": "会议", "magazine": "杂志",
                  "patent": "专利", "editorial": "社论", "book": "专著",
                  "chapter": "书籍章节"},
        "empty_pubs": "没有符合条件的论文。",
        "footnote_pubs": "\u2020 该条目暂无直接 PDF 链接，按钮将打开公共论文库以下载全文。带星号（\u2605）的为代表性论文。",
        "meta_repo": "{n} 篇全文 PDF 可供下载",
        "intro_repo": "全部全文 PDF 托管于本站，下载不依赖 Google Drive 或出版社页面。在上方输入论文标题即可搜索并下载对应 PDF——列表默认隐藏，搜索后显示。",
        "sr_search_repo": "搜索 PDF 文库",
        "search_repo": "搜索 PDF 标题…",
        "empty_repo": "没有符合条件的 PDF。",
        "footnote_repo": "PDF 按原文件提供。再次分发时请遵守出版社版权与开放获取条款。",
        "repo_hint": "在上方输入标题以搜索全文 PDF，匹配的文件会在此显示并提供下载。",
        "undated": "早期论文及年份未确认的全文",
        "sec_conference": "会议论文",
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
        # 单篇论文详情页
        "detail_back": "返回论文列表",
        "detail_output": "研究成果",
        "detail_output_journal": "期刊论文",
        "detail_output_conf": "会议论文",
        "detail_output_magazine": "杂志文章",
        "detail_output_other": "出版物",
        "detail_orig_lang": "原文语言",
        "detail_lang_val": "英文",
        "detail_lang_zh": "中文",
        "detail_pages": "页码（起-止）",
        "detail_journal": "期刊",
        "detail_volume": "卷",
        "detail_issue": "期",
        "detail_pubdate": "发表日期",
        "detail_doi": "DOI",
        "detail_status": "发表状态",
        "detail_status_val": "已发表",
        "detail_type_label": "文献类型",
        "detail_access": "获取全文",
        "detail_cite": "引用格式",
        "detail_cite_apa": "APA",
        "detail_cite_bibtex": "BibTeX",
        "detail_abstract_note": "全文请通过下方下载链接获取。",
        "detail_abstract": "摘要",
        "detail_keywords": "关键词",
        "detail_scholar": "在 Google Scholar 中查看",
        "detail_other": "其他链接",
        "detail_title_tip": "查看论文详细信息",
    },
}
T = I18N[LANG]


def esc(value):
    return html.escape(str(value), quote=True)


OWNER_RE = re.compile(
    r'\b(?:C\.\s*Liu|Chang[-\s]?jun\s*Liu|Liu\s+Chang[-\s]?jun)\b', re.I
)


def bold_author(value):
    """Escape, then bold every spelling of the owner's name in author lists.

    Enriched CrossRef / PDF records use C. Liu, Changjun Liu, Chang-Jun Liu,
    Liu Changjun and uppercase pinyin LIU CHANGJUN; all must stay bolded.
    """
    s = esc(value)
    return OWNER_RE.sub(lambda m: "<strong>" + m.group(0) + "</strong>", s)


def scholar_url(title):
    # "(in Chinese)" is a display marker for translated Chinese papers; strip it
    # so the Scholar lookup still matches the original publication.
    q = re.sub(r"\s*\(in Chinese\)\s*$", "", title).strip()
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote_plus(q)


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


def render_venue(paper):
    """Render the citation line with IEEE journal names in pure black.

    Only the journal title is emphasised; volume / issue / pages / year keep
    the muted italic style of the surrounding citation. Conference names are
    deliberately left untouched -- the request concerns IEEE *journals*.
    """
    venue = paper.get("venue") or ""
    journal = (paper.get("journal") or "").strip()
    ptype = (paper.get("type") or "journal").lower()
    name = ""
    if journal and "IEEE" in journal.upper() and venue.upper().startswith(journal.upper()):
        name = journal
    elif ptype in ("journal", "magazine"):
        head = venue.split(",")[0].strip()
        if "IEEE" in head.upper():
            name = head
    if not name:
        return esc(venue)
    return (
        f'<span class="journal-black">{esc(name)}</span>'
        f'{esc(venue[len(name):])}'
    )


def render_paper(paper, index):
    title = paper["title"]
    authors = paper["authors"]
    venue = paper["venue"]
    ptype = paper.get("type", "journal")
    ptype_label = T["types"].get(ptype, ptype.title())
    pdf_url, pdf_label, pdf_tip = pdf_target(paper)
    search_blob = " ".join([
        title, authors, venue, ptype_label, str(paper["year"]),
        str(paper.get("journal", "")), str(paper.get("volume", "")),
        str(paper.get("issue", "")), str(paper.get("pages", "")),
    ]).lower()

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
        <div class="paper-title">{star}<a class="paper-link" href="{esc(detail_href(paper))}" title="{esc(T.get("detail_title_tip", "Publication details"))}">{esc(title)}</a></div>
        <div class="paper-authors">{bold_author(authors)}</div>
        <div class="paper-venue">{render_venue(paper)}</div>
        <div class="paper-actions">{''.join(links)}</div>
      </li>'''


def prestige_key(paper):
    """Ordering within a single year.

    IEEE Magazine first, then IEEE Transactions, then IEEE Letters, then other
    IEEE venues, other journals, and finally conference papers (always last).
    Python's sort is stable, so entries sharing a tier keep their data order.
    """
    venue = ((paper.get("venue") or "") + " " + (paper.get("journal") or "")).lower()
    ptype = (paper.get("type") or "journal").lower()
    if ptype == "conference":
        return 90
    if "ieee" in venue:
        if "magazine" in venue:
            return 0
        if "transactions" in venue or "ieee trans" in venue:
            return 1
        if "letters" in venue:
            return 2
        return 3
    if "letters" in venue:
        return 4
    if ptype == "magazine":
        return 5
    if ptype == "editorial":
        return 6
    if ptype == "patent":
        return 7
    return 10


def render_years():
    grouped = OrderedDict()
    for p in PAPERS:
        grouped.setdefault(p["year"], []).append(p)
    # newest year first, undated last
    grouped = OrderedDict(
        sorted(grouped.items(), key=lambda kv: (kv[0] is None, -(kv[0] or 0)))
    )

    out = []
    counter = 1
    for year, items in grouped.items():
        ykey = year if year is not None else "undated"
        ylabel = year if year is not None else T["undated"]
        # one continuous list per year: conference papers sit after journal
        # papers without a separate subheading or a second <ol>
        items = sorted(items, key=prestige_key)
        rows = "\n".join(render_paper(p, counter + i) for i, p in enumerate(items))
        # The year itself links to that year's dedicated archive page so Google
        # (and readers) can reach every paper and PDF for the year in one click.
        href = year_page_url(LANG, str(ykey))
        out.append(f'''    <section class="year-group" data-year="{ykey}">
      <h3 class="year-heading"><a class="year-link" href="{esc(href)}" title="{esc(T["year_link_tip"].format(year=ylabel))}">{esc(ylabel)}</a><span class="year-count">{len(items)}</span></h3>
      <ol class="papers" start="{counter}">
{rows}
      </ol>
    </section>''')
        counter += len(items)
    return "\n".join(out), len(grouped)


# ---------------------------------------------------------------------------
# Per-year archive pages.  Every year gets its own crawlable HTML page in both
# languages, listing every paper AND every full-text PDF for that year, so each
# PDF has a static, visible, indexable link instead of living only inside the
# JavaScript-driven repository on the homepage.
# ---------------------------------------------------------------------------
YEAR_TEXT = {
    "en": {
        "title": "Publications in {year}",
        "desc": "All {n} papers by Changjun Liu published in {year}, with authors, journal details and free full-text PDF downloads.",
        "h_papers": "Papers published in {year}",
        "h_pdfs": "All {m} full-text PDFs for {year}",
        "back": "Back to homepage",
        "other_lang": "中文版 / Chinese",
        "nav": "Browse all years",
        "undated": "Earlier works & undated full texts",
        "undated_short": "Earlier",
        "tip": "View all {year} papers and PDFs",
        "meta": "{n} papers &middot; {m} full-text PDFs",
        "no_papers": "No dated publications in this group; the full texts are listed below.",
        "pdf_hint": "Click any title to download the PDF.",
        "undated_h1": "Earlier works & undated full texts",
        "undated_desc": "Earlier works and full texts whose publication year is not confirmed, with free full-text PDF downloads.",
        "undated_papers_h": "Papers in this group",
        "undated_pdfs_h": "All {m} full-text PDFs in this group",
    },
    "zh": {
        "title": "{year} 年发表论文",
        "desc": "刘长军 {year} 年发表的 {n} 篇论文，含作者、期刊卷期页码信息及全文 PDF 下载。",
        "h_papers": "{year} 年发表论文",
        "h_pdfs": "{year} 年全部 {m} 个全文 PDF",
        "back": "返回中文主页",
        "other_lang": "English",
        "nav": "按年份浏览",
        "undated": "早期论文及年份未确认的全文",
        "undated_short": "早期",
        "tip": "查看 {year} 年全部论文与 PDF",
        "meta": "{n} 篇论文 &middot; {m} 个全文 PDF",
        "no_papers": "该分组没有标注年份的论文，全文 PDF 列于下方。",
        "pdf_hint": "点击标题即可下载 PDF。",
        "undated_h1": "早期论文及年份未确认的全文",
        "undated_desc": "早期论文及发表年份尚未确认的全文，均可免费下载 PDF。",
        "undated_papers_h": "该分组论文",
        "undated_pdfs_h": "该分组全部 {m} 个全文 PDF",
    },
}


def year_keys():
    """Dated years (newest first) plus one page for undated full texts."""
    years = sorted({int(p["year"]) for p in PAPERS if p["year"] is not None}, reverse=True)
    return [str(y) for y in years] + ["undated"]


def year_page_url(lang, key):
    return SITE_URL + ("zh/years/" if lang == "zh" else "years/") + str(key) + ".html"


def abs_pdf_url(path):
    return SITE_URL + urllib.parse.quote(path, safe="/")


# ---------------------------------------------------------------------------
# Single-paper detail pages.  Each publication gets its own crawlable HTML page
# with Google Scholar / citation meta tags, modelled on institutional research
# portals (title, authors, research output metadata, DOI, full text, cite this).
# ---------------------------------------------------------------------------
def _base_slug(paper):
    title = re.sub(r"\s*\(in Chinese\)\s*$", "", paper["title"])
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = slug[:90].rstrip("-")
    if not slug:
        slug = "paper"
    year = paper.get("year") or "nd"
    return "%s-%s" % (year, slug)


def paper_slug(paper):
    """Stable, SEO-friendly, collision-free slug: <year>-<normalized title>[-n]."""
    base = _base_slug(paper)
    # Duplicate publication records share a title; give each a unique page.
    dupes = [p for p in PAPERS if _base_slug(p) == base]
    if len(dupes) > 1:
        idx = dupes.index(paper)
        if idx > 0:
            return "%s-%d" % (base, idx + 1)
    return base


def detail_url(paper, lang="en"):
    prefix = ZH_URL if lang == "zh" else EN_URL
    return prefix + ("pub/" if lang == "zh" else "publications/") + paper_slug(paper) + ".html"


def detail_href(paper):
    """Relative href used from the home page (en root / zh subdir)."""
    base = "pub/" if LANG == "zh" else "publications/"
    return base + paper_slug(paper) + ".html"


def split_authors(authors):
    """Normalise 'Z. He, L. Yan, and C. Liu' -> ['Z. He', 'L. Yan', 'C. Liu']."""
    s = re.sub(r"\s+and\s+", ", ", authors)
    return [a.strip() for a in s.split(",") if a.strip()]


def cite_apa(paper):
    authors = paper.get("authors", "")
    year = paper.get("year", "")
    title = re.sub(r"\s*\(in Chinese\)\s*$", "", paper["title"])
    journal = paper.get("journal") or (paper.get("venue") or "").split(",")[0].strip()
    vol = paper.get("volume") or ""
    issue = paper.get("issue") or ""
    pages = paper.get("pages") or ""
    doi = paper.get("doi") or ""
    bits = "%s (%s). %s" % (authors, year, title)
    if journal:
        bits += ". <em>%s</em>" % journal
    if vol:
        bits += ", <em>%s</em>" % vol
    if issue:
        bits += "(%s)" % issue
    if pages:
        bits += ", %s" % pages
    bits += "."
    if doi:
        bits += " https://doi.org/%s" % doi
    return bits


def cite_ieee(paper):
    """IEEE reference style: A. Author, B. Author, "Title," Journal, vol. x, no. y, pp. a-b, Year.
    Authors are already stored as 'Z. He, H. He, and C. Liu' (IEEE-style initials)."""
    authors = re.sub(r"\s+and\s+", ", ", paper.get("authors", "")).replace(", and ", ", ")
    authors = re.sub(r",\s*,", ",", authors)
    title = re.sub(r"\s*\(in Chinese\)\s*$", "", paper["title"])
    journal = paper.get("journal") or (paper.get("venue") or "").split(",")[0].strip()
    vol = paper.get("volume") or ""
    issue = paper.get("issue") or ""
    pages = paper.get("pages") or ""
    doi = paper.get("doi") or ""
    year = paper.get("year") or ""
    bits = "%s, \"%s\"" % (authors, title)
    if journal:
        bits += ", <em>%s</em>" % journal
    if vol:
        bits += ", vol. %s" % vol
    if issue:
        bits += ", no. %s" % issue
    if pages:
        pages = pages.replace("\u2013", "-").replace("\u2014", "-")
        bits += ", pp. %s" % pages
    if year:
        bits += ", %s" % year
    bits += "."
    if doi:
        bits += " doi: %s." % doi
    return bits


def cite_bibtex(paper):
    authors = " and ".join(split_authors(paper.get("authors", "")))
    year = str(paper.get("year") or "")
    title = re.sub(r"\s*\(in Chinese\)\s*$", "", paper["title"])
    journal = paper.get("journal") or (paper.get("venue") or "").split(",")[0].strip()
    key = re.sub(r"[^a-zA-Z]", "", paper.get("authors", "").split(",")[0])[:6].lower() + year
    etype = "article" if paper.get("type", "journal") in ("journal", "magazine") else "inproceedings"
    lines = ["@%s{%s," % (etype, key)]
    lines.append("  author    = {%s}," % authors)
    lines.append("  title     = {%s}," % title)
    if journal:
        lines.append("  journal   = {%s}," % journal)
    if paper.get("volume"):
        lines.append("  volume    = {%s}," % paper["volume"])
    if paper.get("issue"):
        lines.append("  number    = {%s}," % paper["issue"])
    if paper.get("pages"):
        lines.append("  pages     = {%s}," % paper["pages"])
    if year:
        lines.append("  year      = {%s}," % year)
    if paper.get("doi"):
        lines.append("  doi       = {%s}," % paper["doi"])
    lines.append("}")
    return "\n".join(lines)


def render_year_paper(p, idx):
    """A paper row for an archive page; PDF URLs are absolute (page lives in /years/)."""
    ptype = p.get("type", "journal")
    label = T["types"].get(ptype, ptype.title())
    pdf = abs_pdf_url(p["local"]) if p.get("local") else (p.get("pdf") or DRIVE)
    links = [
        f'<a class="btn btn-pdf" href="{esc(pdf)}" target="_blank" rel="noopener">PDF</a>'
    ]
    if p.get("doi"):
        links.append(
            f'<a class="btn btn-ghost" href="{esc("https://doi.org/" + p["doi"])}" '
            'target="_blank" rel="noopener">DOI</a>'
        )
    links.append(
        f'<a class="btn btn-ghost" href="{esc(scholar_url(p["title"]))}" '
        f'target="_blank" rel="noopener">{esc(T["btn_scholar"])}</a>'
    )
    star = (
        '<span class="star" aria-label="Selected publication">\u2605</span> '
        if p.get("selected") else ""
    )
    detail_href_year = "../" + ("pub/" if LANG == "zh" else "publications/") + paper_slug(p) + ".html"
    return f'''      <li class="paper">
        <div class="paper-head"><span class="idx">{idx:02d}</span><span class="badge">{esc(label)}</span></div>
        <div class="paper-title">{star}<a class="paper-link" href="{esc(detail_href_year)}">{esc(p["title"])}</a></div>
        <div class="paper-authors">{bold_author(p["authors"])}</div>
        <div class="paper-venue">{render_venue(p)}</div>
        <div class="paper-actions">{''.join(links)}</div>
      </li>'''


def render_year_page(key):
    yt = YEAR_TEXT[LANG]
    year = None if key == "undated" else int(key)
    label = yt["undated"] if year is None else str(year)
    papers = sorted([p for p in PAPERS if p["year"] == year], key=prestige_key)
    lib = [it for it in DATA.get("full_pdf_library", []) if it.get("year") == year]
    n_papers, n_pdfs = len(papers), len(lib)

    canonical = year_page_url(LANG, key)
    en_url, zh_url = year_page_url("en", key), year_page_url("zh", key)
    home = ZH_URL if LANG == "zh" else EN_URL
    other = zh_url if LANG == "en" else en_url
    css = SITE_URL + ("zh/assets/style.css" if LANG == "zh" else "assets/style.css")
    lang_attr = "zh-CN" if LANG == "zh" else "en"
    own_locale = "zh_CN" if LANG == "zh" else "en_US"

    nav = "\n".join(
        '      <a class="yp-nav-link%s" href="%s">%s</a>'
        % (" is-current" if k == key else "",
           esc(year_page_url(LANG, k)),
           esc(yt["undated_short"] if k == "undated" else k))
        for k in year_keys()
    )
    paper_rows = "\n".join(render_year_paper(p, i + 1) for i, p in enumerate(papers))
    pdf_rows = "\n".join(
        '        <li><a href="%s" target="_blank" rel="noopener">%s'
        '<span class="yp-dl">PDF \u2193</span></a></li>'
        % (esc(abs_pdf_url(it["file"])), esc(it["title"]))
        for it in lib
    )
    no_papers = "" if n_papers else '<p class="muted">%s</p>' % esc(yt["no_papers"])

    # Undated group reads differently: it is not "papers published in {year}".
    if year is None:
        title_txt = yt["undated_h1"]
        desc_txt = yt["undated_desc"]
        h_papers = yt["undated_papers_h"]
        h_pdfs = yt["undated_pdfs_h"].format(m=n_pdfs)
    else:
        title_txt = yt["title"].format(year=label)
        desc_txt = yt["desc"].format(n=n_papers, year=label)
        h_papers = yt["h_papers"].format(year=label)
        h_pdfs = yt["h_pdfs"].format(m=n_pdfs, year=label)

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title_txt,
        "description": desc_txt,
        "url": canonical,
        "inLanguage": lang_attr,
        "isPartOf": {"@type": "WebSite", "url": SITE_URL, "name": PROFILE["name"]},
        "about": {"@type": "Person", "name": PROFILE["name"],
                  "affiliation": PROFILE["affiliation"]},
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": n_papers,
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1,
                 "item": dict(
                     {"@type": "ScholarlyArticle", "headline": p["title"],
                      "author": p["authors"]},
                     **({"datePublished": str(year)} if year else {}),
                     **({"url": abs_pdf_url(p["local"])} if p.get("local") else {}),
                 )}
                for i, p in enumerate(papers)
            ],
        },
    }
    jsonld = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
    return f'''<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title_txt)} | {esc(P["name"])}</title>
  <meta name="description" content="{esc(desc_txt)}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="alternate" hreflang="en" href="{esc(en_url)}">
  <link rel="alternate" hreflang="zh-Hans" href="{esc(zh_url)}">
  <link rel="alternate" hreflang="x-default" href="{esc(en_url)}">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(title_txt)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:locale" content="{own_locale}">
  <meta property="og:site_name" content="{esc(P["name"])} | Sichuan University">
  <link rel="stylesheet" href="{esc(css)}">
  <script type="application/ld+json">{jsonld}</script>
</head>
<body class="yp-body">
<div class="wrap yp-wrap">
  <header class="yp-header">
    <nav class="yp-topnav">
      <a href="{esc(home)}">\u2190 {esc(yt["back"])}</a>
      <span class="yp-sep">|</span>
      <a href="{esc(other)}">{esc(yt["other_lang"])}</a>
    </nav>
    <h1>{esc(title_txt)}</h1>
    <p class="yp-meta">{yt["meta"].format(n=n_papers, m=n_pdfs)}</p>
    <nav class="yp-nav" aria-label="{esc(yt["nav"])}">
{nav}
    </nav>
  </header>

  <section class="card yp-section">
    <h2>{esc(h_papers)}</h2>
    {no_papers}
    <ol class="papers">
{paper_rows}
    </ol>
  </section>

  <section class="card yp-section">
    <h2>{esc(h_pdfs)}</h2>
    <p class="muted">{esc(yt["pdf_hint"])}</p>
    <ul class="yp-pdfs">
{pdf_rows}
    </ul>
  </section>

  <footer class="footer">
    <div class="wrap"><span>&copy; {esc(P["name"])}</span></div>
  </footer>
</div>
</body>
</html>
'''


def write_year_pages():
    ydir = OUT / "years"
    ydir.mkdir(parents=True, exist_ok=True)
    keys = year_keys()
    for k in keys:
        (ydir / (k + ".html")).write_text(render_year_page(k), encoding="utf-8")
    return len(keys)


def render_detail_page(paper):
    """A single, self-contained, crawlable page for one publication."""
    title_display = paper["title"]  # keeps the "(in Chinese)" marker for readers
    title = re.sub(r"\s*\(in Chinese\)\s*$", "", paper["title"])  # clean, for citations/SEO
    in_chinese = (bool(paper.get("in_chinese")) or title_display != title
                  or bool(paper.get("title_zh")) or bool(paper.get("abstract_zh")))
    # On the Chinese page, a Chinese-language paper shows its original Chinese
    # title/authors/journal; everywhere else uses the English metadata.
    show_zh = in_chinese and LANG == "zh" and paper.get("title_zh")
    if show_zh:
        head_title = paper["title_zh"]
        head_authors = paper.get("authors_zh") or paper.get("authors", "")
        head_journal = paper.get("journal_zh") or (paper.get("journal") or "")
    else:
        head_title = title_display
        head_authors = ""
        head_journal = ""
    # Abstract & keywords: prefer Chinese on the Chinese page for zh papers.
    if LANG == "zh" and paper.get("abstract_zh"):
        abstract_text = paper["abstract_zh"]
        keywords_text = paper.get("keywords_zh", "")
    else:
        abstract_text = paper.get("abstract_en", "")
        keywords_text = paper.get("keywords_en", "")
    # JSON-LD / Scholar meta use the clean English title regardless of display
    ptype = (paper.get("type") or "journal").lower()
    if ptype == "conference":
        output_label = T["detail_output_conf"]
    elif ptype == "magazine":
        output_label = T["detail_output_magazine"]
    elif ptype == "journal":
        output_label = T["detail_output_journal"]
    else:
        output_label = T["detail_output_other"]
    type_label = T["types"].get(ptype, ptype.title())
    star_mark = ("\u2605 " if paper.get("selected") else "")

    journal = (paper.get("journal") or (paper.get("venue") or "").split(",")[0].strip())
    vol = paper.get("volume") or ""
    issue = paper.get("issue") or ""
    pages = paper.get("pages") or ""
    doi = paper.get("doi") or ""
    year = paper.get("year") or ""
    authors = paper.get("authors", "")
    author_list = split_authors(authors)

    canonical = detail_url(paper, LANG)
    en_url = detail_url(paper, "en")
    zh_url = detail_url(paper, "zh")
    home = ZH_URL if LANG == "zh" else EN_URL
    lang_attr = "zh-CN" if LANG == "zh" else "en"
    own_locale = "zh_CN" if LANG == "zh" else "en_US"
    css = SITE_URL + ("zh/assets/style.css" if LANG == "zh" else "assets/style.css")
    desc = "%s. %s. %s %s. %s" % (authors, title, journal, year, doi)
    page_title_txt = "%s | %s | Sichuan University" % (title, P["name"])

    # Primary full-text link (absolute, works from /publications/ directory)
    if paper.get("local"):
        pdf_url = abs_pdf_url(paper["local"])
    elif paper.get("pdf"):
        pdf_url = paper["pdf"]
    else:
        pdf_url = DRIVE

    links_html = [
        '<a class="btn btn-pdf" href="%s" target="_blank" rel="noopener">%s \u2193</a>'
        % (esc(pdf_url), esc("PDF" if not paper.get("local") and not paper.get("pdf") else "PDF"))
    ]
    if doi:
        links_html.append(
            '<a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">DOI \u2197</a>'
            % esc("https://doi.org/" + doi))
    links_html.append(
        '<a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">%s \u2197</a>'
        % (esc(scholar_url(title)), esc(T["detail_scholar"])))
    if paper.get("local") and paper.get("pdf"):
        links_html.append(
            '<a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">%s \u2197</a>'
            % (esc(paper["pdf"]), esc(T["btn_mirror"])))

    # Metadata definition table
    meta_rows = []
    meta_rows.append((T["detail_output"], output_label + " \u203A " + type_label))
    meta_rows.append((T["detail_orig_lang"], T["detail_lang_zh"] if in_chinese else T["detail_lang_val"]))
    if show_zh and head_journal:
        meta_rows.append((T["detail_journal"], head_journal))
    elif journal:
        meta_rows.append((T["detail_journal"], journal))
    if vol:
        meta_rows.append((T["detail_volume"], vol))
    if issue:
        meta_rows.append((T["detail_issue"], issue))
    if pages:
        meta_rows.append((T["detail_pages"], pages))
    if year:
        meta_rows.append((T["detail_pubdate"], str(year)))
    if doi:
        meta_rows.append((T["detail_doi"], '<a href="%s" target="_blank" rel="noopener">https://doi.org/%s</a>'
                          % (esc("https://doi.org/" + doi), esc(doi))))
    meta_rows.append((T["detail_status"], T["detail_status_val"]))
    meta_html = "\n".join(
        '        <div class="dt-row"><dt>%s</dt><dd>%s</dd></div>' % (esc(k), v if v.startswith("<a ") else esc(v))
        for k, v in meta_rows
    )

    display_author_list = split_authors(head_authors) if show_zh else author_list
    authors_html = ", ".join(
        ("<strong>" + esc(a) + "</strong>") if (OWNER_RE.search(a) or (show_zh and "刘长军" in a)) else esc(a)
        for a in display_author_list
    )

    # Abstract & keywords section (only when data is available)
    abstract_html = ""
    if abstract_text:
        kw_html = ""
        if keywords_text:
            kws = [k.strip() for k in re.split(r"[;,；，]", keywords_text) if k.strip()]
            kw_html = '<p class="dt-keywords"><strong>%s:</strong> %s</p>' % (
                esc(T["detail_keywords"]), esc(", ".join(kws)))
        abstract_html = '''    <section class="dt-section dt-abstract">
      <h2>{h}</h2>
      <p class="dt-abstract-text">{body}</p>
      {kw}
    </section>
'''.format(h=esc(T["detail_abstract"]), body=esc(abstract_text), kw=kw_html)
    # English papers use IEEE style; Chinese-language papers keep APA.
    if in_chinese:
        primary_cite_label = T["detail_cite_apa"]
        primary_cite = cite_apa(paper)
    else:
        primary_cite_label = "IEEE"
        primary_cite = cite_ieee(paper)
    bibtex = cite_bibtex(paper)

    # ---- Google Scholar / citation meta tags (the key to being indexed) ----
    cite_meta = ['  <meta name="citation_title" content="%s">' % esc(title)]
    for a in author_list:
        cite_meta.append('  <meta name="citation_author" content="%s">' % esc(a))
    if year:
        cite_meta.append('  <meta name="citation_publication_date" content="%s">' % esc(year))
    if journal:
        cite_meta.append('  <meta name="citation_journal_title" content="%s">' % esc(journal))
    if vol:
        cite_meta.append('  <meta name="citation_volume" content="%s">' % esc(vol))
    if issue:
        cite_meta.append('  <meta name="citation_issue" content="%s">' % esc(issue))
    if pages:
        parts = re.split(r"[\u2013\u2014\-]", pages, maxsplit=1)
        cite_meta.append('  <meta name="citation_firstpage" content="%s">' % esc(parts[0].strip()))
        if len(parts) > 1:
            cite_meta.append('  <meta name="citation_lastpage" content="%s">' % esc(parts[1].strip()))
    if doi:
        cite_meta.append('  <meta name="citation_doi" content="%s">' % esc(doi))
    if paper.get("local"):
        cite_meta.append('  <meta name="citation_pdf_url" content="%s">' % esc(abs_pdf_url(paper["local"])))
    cite_meta.append('  <meta name="citation_language" content="%s">' % ("zh" if in_chinese else "en"))
    cite_meta_html = "\n".join(cite_meta)

    # ---- schema.org ScholarlyArticle JSON-LD ----
    schema = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "headline": title,
        "author": [{"@type": "Person", "name": a} for a in author_list],
        "datePublished": str(year) if year else None,
        "inLanguage": "zh" if in_chinese else "en",
        "url": canonical,
        "isPartOf": {"@type": "WebSite", "url": SITE_URL, "name": P["name"]},
        "publisher": {"@type": "CollegeOrUniversity", "name": P["affiliation"]},
        "about": {"@type": "Person", "name": P["name"],
                  "affiliation": P["affiliation"]},
    }
    if journal:
        schema["periodical"] = {"@type": "Periodical", "name": journal}
    if doi:
        schema["identifier"] = {"@type": "PropertyValue", "propertyID": "doi", "value": doi}
        schema["sameAs"] = "https://doi.org/" + doi
    if paper.get("local"):
        schema["fullTextUrl"] = abs_pdf_url(paper["local"])
    schema = {k: v for k, v in schema.items() if v is not None}
    jsonld = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")

    return f'''<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title_txt)}</title>
  <meta name="description" content="{esc(desc)}">
  <meta name="author" content="{esc(authors)}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="alternate" hreflang="en" href="{esc(en_url)}">
  <link rel="alternate" hreflang="zh-Hans" href="{esc(zh_url)}">
  <link rel="alternate" hreflang="x-default" href="{esc(en_url)}">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:locale" content="{own_locale}">
  <meta property="og:site_name" content="{esc(P["name"])} | Sichuan University">
  <meta property="og:description" content="{esc(desc)}">
{cite_meta_html}
  <link rel="stylesheet" href="{esc(css)}">
  <script type="application/ld+json">{jsonld}</script>
</head>
<body class="dt-body">
<div class="dt-wrap">
  <nav class="dt-topnav">
    <a href="{esc(home + '#publications')}">\u2190 {esc(T["detail_back"])}</a>
    <span class="dt-sep">|</span>
    <a href="{esc(zh_url if LANG == "en" else en_url)}">{esc(T["alt_version"])}</a>
  </nav>

  <article class="dt-card">
    <div class="dt-badge">{esc(type_label)}</div>
    <h1 class="dt-title">{star_mark}{esc(head_title)}</h1>
    <p class="dt-authors">{authors_html}</p>
    <p class="dt-aff">{esc(P["affiliation"])}</p>

    <section class="dt-section">
      <h2>{esc(T["detail_output"])}</h2>
      <dl class="dt-meta">
{meta_html}
      </dl>
    </section>
{abstract_html}
    <section class="dt-section">
      <h2>{esc(T["detail_access"])}</h2>
      <p class="dt-note">{esc(T["detail_abstract_note"])}</p>
      <div class="dt-actions">{''.join(links_html)}</div>
    </section>

    <section class="dt-section">
      <h2>{esc(T["detail_cite"])}</h2>
      <div class="dt-cite">
        <h3>{esc(primary_cite_label)}</h3>
        <p class="dt-cite-text">{primary_cite}</p>
        <h3>{esc(T["detail_cite_bibtex"])}</h3>
        <pre class="dt-cite-code">{esc(bibtex)}</pre>
      </div>
    </section>
  </article>

  <footer class="dt-footer">
    <a href="{esc(home + '#publications')}">\u2190 {esc(T["detail_back"])}</a>
  </footer>
</div>
</body>
</html>
'''


def write_detail_pages():
    """Write one detail page per publication, in the current language."""
    ddir = OUT / ("pub" if LANG == "zh" else "publications")
    ddir.mkdir(parents=True, exist_ok=True)
    for paper in PAPERS:
        (ddir / (paper_slug(paper) + ".html")).write_text(
            render_detail_page(paper), encoding="utf-8")
    return len(PAPERS)


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
    if PHOTO_PATH.exists():
        return (
            f'<img class="avatar" src="assets/{PHOTO_NAME}" alt="{esc(P["name"])}" '
            'width="108" height="108" loading="eager" fetchpriority="high" decoding="async">'
        )
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
    if PHOTO_PATH.exists():
        lines += [
            f'  <meta property="og:image" content="{esc(PHOTO_URL)}">',
            '  <meta property="og:image:type" content="image/jpeg">',
            '  <meta property="og:image:width" content="1024">',
            '  <meta property="og:image:height" content="1024">',
            f'  <meta property="og:image:alt" content="{esc(P["name"])}">',
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
    if PHOTO_PATH.exists():
        schema["image"] = PHOTO_URL
    if LANG == "zh":
        schema["alternateName"] = PROFILE["name"]
    return json.dumps(schema, ensure_ascii=False, indent=2)


def render_yearchips():
    years = sorted({p["year"] for p in PAPERS if p["year"] is not None}, reverse=True)
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
            # Keep the search index English-only: file names may still contain
            # CJK characters even though displayed titles are translated.
            blob = " ".join([it["title"], str(year or "")]).lower()
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
    dated = [p["year"] for p in PAPERS if p["year"] is not None]
    year_min = min(dated) if dated else ""
    year_max = max(dated) if dated else ""

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
      <p class="repo-hint" id="repo-hint" hidden>{esc(T["repo_hint"])}</p>
      <div class="pdf-library" id="pdf-library">
{render_pdf_library()}
      </div>
      <p class="library-empty" id="library-empty" hidden>{esc(T["empty_repo"])}</p>
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
        # The Chinese edition is self-contained, so the portrait must be copied too.
        for name in ("style.css", "app.js", PHOTO_NAME):
            src = ROOT / "assets" / name
            if src.exists():
                shutil.copy2(src, OUT / "assets" / name)
    (OUT / "index.html").write_text(doc, encoding="utf-8")
    n_year_pages = write_year_pages()
    n_detail_pages = write_detail_pages()
    print(f"Wrote {OUT / 'index.html'}: {LANG}, {total} publications, {n_years} year groups, "
          f"{n_local} self-hosted PDF links, {n_lib} files in the PDF repository, "
          f"{n_year_pages} year archive pages, {n_detail_pages} detail pages.")


if __name__ == "__main__":
    main()
