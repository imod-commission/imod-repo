#!/usr/bin/env python3
"""Add up the Downloads number of every package: the carried-over old total plus the GitHub
release download counts.

Reads
  * data/yourepo-baseline.json  the old total ("downloads") carried over from the previous source
  * data/package-repos.json     which GitHub repository holds each package's releases
  * the releases of those repositories (GitHub REST API, public data, GITHUB_TOKEN only raises the
    rate limit)

For every package with a repository it adds the download_count of every release asset (all releases,
all versions, drafts skipped) whose name is the name of a file in debs/: <package id>_<version>_<arch>.deb.
These are the files the index points installs at (scripts/release-filenames.py), so the number follows
the files Sileo installs. It also counts direct downloads of those files from the release page, which
GitHub cannot tell apart. Release assets that are not in debs/ (an old version kept only on GitHub) are
not counted: nothing in the index points at them. Installs from packages without a release file come
from GitHub Pages, which has no counter, so they are NOT counted.

Standard library only. Writes a JSON file (never committed; patch-depictions.py reads it) with, per package id,
  total      baseline + releases (or only the one that is known; null when neither is)
  baseline   the carried-over number (or null)
  releases   the sum of release asset downloads (null when not read: no repository, or API error)
  assets     how many release assets were counted
A repository that cannot be read (network, rate limit, 404) only gives a warning: that package
falls back to the baseline and the exit code stays 0, the deploy must not fail for it.

Usage:
  fetch-downloads.py --out downloads.json [--releases-dir DIR] [--api URL]
                     [--baseline data/yourepo-baseline.json] [--repos data/package-repos.json]
                     [--debs debs]
--releases-dir DIR reads DIR/<owner>__<name>.json (a releases API answer) instead of the API (tests).
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAX_PAGES = 20  # 100 releases per page


def warn(msg):
    print("warning: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning::" + msg)


def fetch_releases(api, repo, token):
    releases = []
    for page in range(1, MAX_PAGES + 1):
        url = "%s/repos/%s/releases?per_page=100&page=%d" % (api.rstrip("/"), repo, page)
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "imod-repo-fetch-downloads",
        })
        if token:
            req.add_header("Authorization", "Bearer " + token)
        with urllib.request.urlopen(req, timeout=30) as resp:
            chunk = json.loads(resp.read().decode("utf-8"))
        if not isinstance(chunk, list):
            raise ValueError("unexpected API answer: %r" % (chunk,))
        releases.extend(chunk)
        if len(chunk) < 100:
            break
    return releases


def count_assets(releases, pid, deb_names):
    """(sum of download_count, number of assets) of the assets named <pid>_*.deb that are a file of debs/."""
    total, n = 0, 0
    for rel in releases:
        if rel.get("draft"):
            continue
        for a in rel.get("assets") or []:
            name = a.get("name") or ""
            if name.startswith(pid + "_") and name in deb_names:
                total += int(a.get("download_count") or 0)
                n += 1
    return total, n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--baseline", default=os.path.join(ROOT, "data", "yourepo-baseline.json"))
    ap.add_argument("--repos", default=os.path.join(ROOT, "data", "package-repos.json"))
    ap.add_argument("--debs", default=os.path.join(ROOT, "debs"), help="the folder of the index's files")
    ap.add_argument("--api", default="https://api.github.com")
    ap.add_argument("--releases-dir", help="read releases from DIR/<owner>__<name>.json (tests)")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    baseline = json.load(open(args.baseline, encoding="utf-8")).get("packages") or {}
    repos = json.load(open(args.repos, encoding="utf-8")).get("packages") or {}
    deb_names = {n for n in os.listdir(args.debs) if n.endswith(".deb")}
    token = os.environ.get("GITHUB_TOKEN")

    cache = {}  # repo -> releases list, or None when unreadable
    packages = {}
    for pid in sorted(set(baseline) | set(repos)):
        b = (baseline.get(pid) or {}).get("downloads")
        repo = (repos.get(pid) or {}).get("repo")
        rel_total, n_assets = None, 0
        if repo:
            if repo not in cache:
                try:
                    if args.releases_dir:
                        path = os.path.join(args.releases_dir, repo.replace("/", "__") + ".json")
                        cache[repo] = json.load(open(path, encoding="utf-8"))
                    else:
                        cache[repo] = fetch_releases(args.api, repo, token)
                except (urllib.error.URLError, OSError, ValueError, TimeoutError) as e:
                    cache[repo] = None
                    warn("could not read the releases of %s (%s); %s keeps its carried-over number"
                         % (repo, e, pid))
            if cache[repo] is not None:
                rel_total, n_assets = count_assets(cache[repo], pid, deb_names)
        known = [x for x in (b, rel_total) if x is not None]
        packages[pid] = {
            "total": sum(known) if known else None,
            "baseline": b,
            "releases": rel_total,
            "assets": n_assets,
        }

    result = {"packages": packages}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out == "-":
        sys.stdout.write(text)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        n_ok = sum(1 for v in packages.values() if v["releases"] is not None)
        n_repo = sum(1 for p in packages if (repos.get(p) or {}).get("repo"))
        print("downloads: %d package(s), releases read for %d of %d with a repository -> %s"
              % (len(packages), n_ok, n_repo, args.out))


if __name__ == "__main__":
    main()
