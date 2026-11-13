#!/usr/bin/env python3
"""Bind a custom domain to the academic homepage.

Usage:
    python bind_domain.py example.com            # preview (no files touched)
    python bind_domain.py example.com --apply   # write CNAME, update data, rebuild

What this automates (everything that can be done from this workspace):
  1. Writes a one-line CNAME file at the repo root (GitHub Pages reads it).
  2. Updates profile.site_url / profile_zh.site_url_zh in publications.json.
  3. Rebuilds both editions: index.html (en) and zh/index.html (zh).
  4. Regenerates robots.txt / sitemap.xml so canonical URLs and the Sitemap:
     directive follow the new domain (seo.py).
  5. Prints the exact DNS records and the final GitHub Pages steps.

What still needs YOU (cannot be done from here):
  * Add the DNS records at your domain registrar (requires your login there).
  * Turn on "Enforce HTTPS" in GitHub -> Settings -> Pages (after DNS propagates).
  * Push the updated files (see the command printed at the end).

Note: the free Tencent/WorkBuddy one-click hosting that serves the Chinese
site does NOT support custom domains. A custom domain therefore points at the
GitHub Pages repository, which then serves BOTH editions:
    https://<domain>/      -> English
    https://<domain>/zh/   -> Chinese
The Chinese site keeps its PDF links on the stable github.io absolute URL, so
downloads keep working even before the new domain propagates.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "publications.json"
DOMAIN_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+(\.)?$"
)

GITHUB_PAGES_A = ["185.199.108.153", "185.199.109.153",
                  "185.199.110.153", "185.199.111.153"]
GITHUB_PAGES_AAAA = ["2606:50c0:8000::153", "2606:50c0:8001::153",
                     "2606:50c0:8002::153", "2606:50c0:8003::153"]
CNAME_TARGET = "scumicrowave.github.io"  # project site: no /homepage in the target


def normalize(raw):
    d = raw.strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = d.split("/")[0].split(":")[0].rstrip(".")
    if not DOMAIN_RE.match(d):
        sys.exit("Invalid domain: %r\nExpected something like example.com or cn.example.com" % raw)
    return d


def apex_of(d):
    """Best-effort apex for the DNS hints (handles common two-level TLDs)."""
    parts = d.split(".")
    two_level = {"com.cn", "net.cn", "org.cn", "edu.cn", "ac.cn", "gov.cn",
                 "co.uk", "org.uk", "ac.uk", "com.hk", "com.tw", "co.jp"}
    if len(parts) >= 3 and ".".join(parts[-2:]) in two_level:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else d


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    if not args:
        sys.exit(__doc__)
    domain = normalize(args[0])
    apex = apex_of(domain)
    is_apex = domain == apex

    print("Domain      : %s" % domain)
    print("Apex        : %s" % apex)
    print("Mode        : %s" % ("APPLY (files will be written)" if apply else "preview (dry-run)"))
    print()

    if apply:
        (ROOT / "CNAME").write_text(domain + "\n", encoding="utf-8")
        print("[ok] wrote CNAME -> %s" % domain)

        data = json.loads(DATA.read_text(encoding="utf-8"))
        data["profile"]["site_url"] = "https://%s/" % domain
        zh = data.get("profile_zh")
        if zh is not None:
            zh["site_url_zh"] = "https://%s/zh/" % domain
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("[ok] updated publications.json site_url")

        for cmd in ([sys.executable, "build.py"],
                    [sys.executable, "build.py", "--lang", "zh"],
                    [sys.executable, "seo.py"]):
            subprocess.run(cmd, cwd=ROOT, check=True)
        print("[ok] rebuilt index.html + zh/index.html + sitemap.xml/robots.txt")
        print()

    print("=" * 68)
    print("STEP 1  Add these DNS records at your registrar (%s)" % apex)
    print("=" * 68)
    if is_apex:
        print("  A     @    -> %s" % GITHUB_PAGES_A[0])
        for ip in GITHUB_PAGES_A[1:]:
            print("  A     @    -> %s" % ip)
        print("  (optional IPv6)")
        for ip in GITHUB_PAGES_AAAA:
            print("  AAAA  @    -> %s" % ip)
        print("  CNAME www  -> %s" % CNAME_TARGET)
        print()
        print("  With both apex and www configured, GitHub redirects one to the other.")
    else:
        print("  CNAME %s  -> %s" % (domain.split(".")[0], CNAME_TARGET))
    print()
    print("  IMPORTANT: the CNAME target must be exactly '%s'." % CNAME_TARGET)
    print("  Do NOT append /homepage, and do not point a subdomain at the apex.")
    print("  Remove any default/wildcard records; DNS may take up to 24h.")
    print()

    print("=" * 68)
    print("STEP 2  GitHub Pages settings (once DNS is live)")
    print("=" * 68)
    print("  Repo scumicrowave/homepage -> Settings -> Pages -> Custom domain")
    print("  Enter: %s   -> Save" % domain)
    print("  Then tick 'Enforce HTTPS' (may take up to 24h after DNS).")
    print("  The root CNAME file written by --apply is the same setting in code.")
    print()

    print("=" * 68)
    print("STEP 3  Push the updated files")
    print("=" * 68)
    print("  GITHUB_TOKEN=<PAT> python deploy_api.py")
    print("  (Uploads CNAME, the rebuilt pages and zh/ in one commit.)")
    print()
    print("  Result:  https://%s/       English" % domain)
    print("           https://%s/zh/    Chinese" % domain)
    print()
    if not apply:
        print("This was a preview. Re-run with --apply to actually write the files.")


if __name__ == "__main__":
    main()
