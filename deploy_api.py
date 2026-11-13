#!/usr/bin/env python3
"""Deploy the academic homepage via the GitHub Git Data API.

Fallback for when `git fetch/push` stalls behind a proxy on large binary files.
All files go into ONE commit; remote-only files are preserved via `base_tree`,
so the push replaces the homepage without deleting anything.

Usage:  GITHUB_TOKEN=ghp_xxx python deploy_api.py
"""
import base64
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOKEN = os.environ.get("GITHUB_TOKEN") or (sys.argv[1] if len(sys.argv) > 1 else "")
if not TOKEN:
    sys.exit("Usage: GITHUB_TOKEN=<PAT> python deploy_api.py")

OWNER, REPO, BRANCH = "scumicrowave", "homepage", "main"
API = "https://api.github.com/repos/%s/%s" % (OWNER, REPO)
CACHE = Path(tempfile.gettempdir()) / "homepage_blob_cache.json"
SKIP = {".git", "_matches.json", "_blob_cache.json", "deploy.log",
        ".DS_Store", "Thumbs.db"}
MESSAGE = "Rebuild academic homepage: 71 publications, 116 self-hosted PDFs"


def api(method, path, payload=None, timeout=180):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "homepage-deploy",
        },
    )
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 502, 503, 504) and attempt < 2:
                time.sleep(4 * (attempt + 1))
                last = e
                continue
            raise SystemExit("API %s %s -> %s: %s" % (method, path, e.code, detail))
        except Exception as e:
            last = e
            if attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
    raise SystemExit("API %s %s failed: %s" % (method, path, last))


def collect():
    out = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in SKIP or part == ".git" for part in rel.parts):
            continue
        if p.suffix == ".zip" or p.name.endswith(".pyc"):
            continue
        out.append((rel.as_posix(), p))
    return out


def upload_blob(item, cached):
    rel, p = item
    raw = p.read_bytes()
    key = rel + "|" + hashlib.sha256(raw).hexdigest()
    if key in cached:
        return rel, key, cached[key]
    res = api("POST", "/git/blobs",
              {"content": base64.b64encode(raw).decode("ascii"),
               "encoding": "base64"},
              timeout=300)
    return rel, key, res["sha"]


def main():
    files = collect()
    print("Uploading %d files (%.1f MB)..." % (
        len(files), sum(p.stat().st_size for _, p in files) / 1e6), flush=True)

    cached = {}
    if CACHE.exists():
        try:
            cached = json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            cached = {}
    snapshot = dict(cached)

    entries = {}
    done = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(upload_blob, it, snapshot) for it in files]
        for fut in as_completed(futs):
            rel, key, sha = fut.result()
            entries[rel] = sha
            cached[key] = sha
            done += 1
            if done % 10 == 0 or done == len(files):
                CACHE.write_text(json.dumps(cached), encoding="utf-8")
                print("  %3d/%d blobs ready" % (done, len(files)), flush=True)

    ref = api("GET", "/git/ref/heads/" + BRANCH)
    base_commit = ref["object"]["sha"]
    base_tree = api("GET", "/git/commits/" + base_commit)["tree"]["sha"]
    print("Base commit %s" % base_commit[:8], flush=True)

    tree = [{"path": rel, "mode": "100644", "type": "blob", "sha": sha}
            for rel, sha in sorted(entries.items())]
    new_tree = api("POST", "/git/trees", {"base_tree": base_tree, "tree": tree})
    print("New tree %s (%d entries)" % (new_tree["sha"][:8], len(tree)), flush=True)

    new_commit = api("POST", "/git/commits",
                     {"message": MESSAGE, "tree": new_tree["sha"],
                      "parents": [base_commit]})
    print("New commit %s" % new_commit["sha"][:8], flush=True)

    api("PATCH", "/git/refs/heads/" + BRANCH,
        {"sha": new_commit["sha"], "force": False})
    print("Updated refs/heads/%s -> %s" % (BRANCH, new_commit["sha"][:8]), flush=True)
    print("Done. https://scumicrowave.github.io/homepage/ will refresh shortly.",
          flush=True)


if __name__ == "__main__":
    main()
