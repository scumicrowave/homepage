#!/usr/bin/env python3
"""Generate robots.txt, sitemap.xml and sitemap-simple.xml from publications.json.

The sitemaps list both language editions plus every self-hosted PDF, so Google
can discover the Chinese page and index the full texts. URLs are percent-encoded
exactly the way build.py encodes them, and the hreflang cluster is declared with
xhtml:link annotations (matching the <link rel=alternate> tags in the pages).

sitemap-simple.xml is a strict-minimal fallback with only <loc> elements and no
extension namespace - useful when a Search Console parser is being difficult.

Usage:
    python seo.py

Re-run after binding a custom domain: it reads profile.site_url, so the sitemap
and the Sitemap: directive in robots.txt follow the new domain automatically.
"""
import json
import urllib.parse
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
SITE = DATA["profile"]["site_url"].rstrip("/") + "/"
EN_URL = SITE
ZH_URL = SITE + "zh/"


def pdf_url(path):
    return SITE + urllib.parse.quote(path, safe="/")


def hreflang_links():
    return (
        '    <xhtml:link rel="alternate" hreflang="en" href="%s"/>\n'
        '    <xhtml:link rel="alternate" hreflang="zh-Hans" href="%s"/>\n'
        '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n'
        % (escape(EN_URL, quote=True), escape(ZH_URL, quote=True), escape(EN_URL, quote=True))
    )


def main():
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "Sitemap: %s\n" % (SITE + "sitemap.xml")
    )
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")

    # (loc, priority, has_hreflang) - one list drives both sitemaps so they can
    # never drift apart. Add a URL here and both files pick it up.
    files = DATA.get("full_pdf_library", [])
    entries = [(EN_URL, "1.0", True), (ZH_URL, "0.9", True)]

    # Every per-year archive page, in both languages. These are the pages that
    # give each PDF a static, crawlable link, so they matter most for indexing.
    papers = DATA.get("publications", [])
    years = sorted({p["year"] for p in papers if p.get("year") is not None}, reverse=True)
    year_keys = [str(y) for y in years] + ["undated"]
    for key in year_keys:
        en_year = SITE + "years/" + key + ".html"
        zh_year = SITE + "zh/years/" + key + ".html"
        entries.append((en_year, "0.7", False))
        entries.append((zh_year, "0.7", False))

    # One crawlable page per publication (both languages), matching build.py's
    # detail pages under /publications/<year>-<slug>.html and /pub/<year>-<slug>.html.
    import re as _re

    def base_slug(paper):
        title = _re.sub(r"\s*\(in Chinese\)\s*$", "", paper["title"])
        slug = _re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:90].rstrip("-")
        if not slug:
            slug = "paper"
        return "%s-%s" % (paper.get("year") or "nd", slug)

    def slug_of(paper):
        base = base_slug(paper)
        dupes = [q for q in papers if base_slug(q) == base]
        if len(dupes) > 1:
            i = dupes.index(paper)
            if i > 0:
                return "%s-%d" % (base, i + 1)
        return base

    for paper in papers:
        entries.append((SITE + "publications/" + slug_of(paper) + ".html", "0.8", False))
        entries.append((SITE + "pub/" + slug_of(paper) + ".html", "0.7", False))

    entries += [(pdf_url(item["file"]), "0.6", False) for item in files]

    # sitemaps.org schema is an ordered sequence: loc, lastmod, changefreq,
    # priority, then extension-namespace elements. Keep xhtml:link AFTER the
    # standard elements so strict parsers (and Search Console) accept the file.
    urls = []
    for loc, priority, has_hreflang in entries:
        block = (
            "  <url>\n"
            "    <loc>%s</loc>\n" % escape(loc, quote=True)
            + "    <priority>%s</priority>\n" % priority
        )
        if has_hreflang:
            block += hreflang_links()
        urls.append(block + "  </url>")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")

    # Strict-minimal fallback: <loc> only, no extension namespace at all.
    # Same URLs, safest possible XML for a picky Search Console parser.
    simple = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(
            "  <url>\n    <loc>%s</loc>\n  </url>\n" % escape(loc, quote=True)
            for loc, _, _ in entries
        )
        + "</urlset>\n"
    )
    (ROOT / "sitemap-simple.xml").write_text(simple, encoding="utf-8")

    print("Wrote robots.txt, sitemap.xml, sitemap-simple.xml: "
          "%d homepages + %d year pages + %d PDFs = %d URLs (base %s)"
          % (2, len(year_keys) * 2, len(files), len(entries), SITE))


if __name__ == "__main__":
    main()
