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
          "%d HTML pages + %d PDFs = %d URLs (base %s)"
          % (2, len(files), len(entries), SITE))


if __name__ == "__main__":
    main()
