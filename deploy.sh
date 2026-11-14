#!/usr/bin/env bash
# One-shot deployment of the academic homepage to GitHub Pages.
#
#   GITHUB_TOKEN=ghp_xxx bash deploy.sh
#   bash deploy.sh ghp_xxx
#
# The token needs the `repo` scope (or a fine-grained token with
# Contents: read + write on scumicrowave/homepage). It is used only for this
# push and is removed from the stored remote URL afterwards.
set -euo pipefail
cd "$(dirname "$0")"

TOKEN="${1:-${GITHUB_TOKEN:-}}"
if [ -z "$TOKEN" ]; then
  echo "Usage: GITHUB_TOKEN=<PAT> bash deploy.sh   (or: bash deploy.sh <PAT>)" >&2
  exit 1
fi

REPO="scumicrowave/homepage"
BRANCH="main"
OWNER="${REPO%%/*}"
REMOTE="https://${OWNER}:${TOKEN}@github.com/${REPO}.git"
export GIT_TERMINAL_PROMPT=0

git init -q
# 211 MB of PDFs exceeds git's default 1 MB HTTP buffer; raise it locally.
git config http.postBuffer 2147483648
git config user.name  "Changjun Liu"
git config user.email "cjliu@scu.edu.cn"
git add -A
git commit -q -m "Rebuild academic homepage: 71 publications, 116 self-hosted PDFs" || echo "Nothing new to commit."
git branch -M "$BRANCH"

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE"
else
  git remote add origin "$REMOTE"
fi

git fetch -q origin "$BRANCH" || true
if git rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1; then
  # Replay the rebuilt site as one commit on top of the existing remote history
  # (no force-push, no "unrelated histories" error).
  git reset --soft "origin/$BRANCH"

  # Keep files that exist only on the remote (old homepage assets / PDFs).
  # Re-add their blobs straight into the index, without writing them back into
  # the local working tree, so the commit replaces index.html but deletes nothing.
  deleted="$(mktemp)"
  git -c core.quotePath=false diff --cached --name-only -z --diff-filter=D > "$deleted"
  while IFS= read -r -d '' f; do
    entry="$(git ls-tree HEAD -- "$f")"
    if [ -z "$entry" ]; then continue; fi
    mode="$(printf '%s' "$entry" | awk '{print $1}')"
    sha="$(printf '%s' "$entry" | awk '{print $3}')"
    git update-index --add --cacheinfo "$mode,$sha,$f"
  done < "$deleted"
  rm -f "$deleted"

  git commit -q -m "Rebuild academic homepage: 71 publications, 116 self-hosted PDFs" || echo "Remote already up to date."
fi

git push -u origin "$BRANCH"

git remote set-url origin "https://github.com/${REPO}.git"
echo "Done. https://scumicrowave.github.io/homepage/ will refresh in a minute or two."
