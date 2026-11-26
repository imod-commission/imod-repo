#!/usr/bin/env python3
"""Packages that live only on a GitHub release, listed in data/release-packages.json.

Each entry names one .deb by its release asset URL and pins the file's size and SHA256:
  {"url": "https://github.com/imod-commission/<repo>/releases/download/<tag>/<file>.deb",
   "size": 488088, "sha256": "<64 hex digits>"}
The package's own fields (Package, Version, Architecture, ...) come from the .deb itself.

fetch ROOT DIR   downloads every entry's asset into DIR. It stops (exit 1) unless the bytes have the
                 listed size and SHA256, and when debs/ holds a file of the same name. Nothing is
                 written to debs/ or to the site.
point ROOT       reads the apt-ftparchive stanzas of DIR (stdin, Filename ./<file>.deb) and writes
                 them (stdout) with Filename set to the entry's release URL. Every stanza must have
                 an entry, and every entry must have a stanza.

Any failure stops the build: the index must never point at a file that is not the listed one.

Usage: release-packages.py fetch ROOT DIR
       release-packages.py point ROOT < Packages.release > Packages.release.pointed
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request

URL_RE = re.compile(
    r"^https://github\.com/imod-commission/[A-Za-z0-9._-]+/releases/download/[^/\s]+/([^/\s]+\.deb)$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
CHUNK = 1 << 16
TIMEOUT = 120


def log(msg):
    print("release-packages: " + msg, file=sys.stderr)


def die(msg):
    print("error: release-packages: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::error::release-packages: " + msg, file=sys.stderr)
    sys.exit(1)


def load(root):
    """Return {file name: (url, size, sha256)} from data/release-packages.json."""
    path = os.path.join(root, "data", "release-packages.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        die("data/release-packages.json cannot be read (%s)" % e)
    items = data.get("packages") if isinstance(data, dict) else None
    if not isinstance(items, list):
        die('data/release-packages.json needs a "packages" list')
    out = {}
    for n, item in enumerate(items, 1):
        try:
            url, size, sha = item["url"], item["size"], item["sha256"]
        except (KeyError, TypeError):
            die("entry %d needs url, size and sha256" % n)
        m = URL_RE.match(url) if isinstance(url, str) else None
        if not m:
            die("entry %d: url must be https://github.com/imod-commission/<repo>/releases/download/"
                "<tag>/<file>.deb, got %r" % (n, url))
        if not isinstance(size, int) or isinstance(size, bool) or not isinstance(sha, str) \
                or not SHA_RE.match(sha):
            die("entry %d: size must be a number and sha256 64 lowercase hex digits" % n)
        fname = m.group(1)
        if fname in out:
            die("%s is listed twice" % fname)
        out[fname] = (url, size, sha)
    return out


def download(url, path):
    # No token: the asset is public, and urllib follows GitHub's redirect to the file itself.
    req = urllib.request.Request(url, headers={"User-Agent": "imod-repo-release-packages"})
    h = hashlib.sha256()
    n = 0
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, open(path, "wb") as out:
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
            n += len(chunk)
            out.write(chunk)
    return n, h.hexdigest()


def fetch(root, dest):
    entries = load(root)
    os.makedirs(dest, exist_ok=True)
    for fname, (url, size, sha) in sorted(entries.items()):
        if os.path.exists(os.path.join(root, "debs", fname)):
            die("%s is in debs/ and also listed on a release; keep one" % fname)
        try:
            got_size, got_sha = download(url, os.path.join(dest, fname))
        except Exception as e:
            die("cannot download %s (%s: %s)" % (url, type(e).__name__, e))
        if (got_size, got_sha) != (size, sha):
            die("%s: the release asset is %d bytes, sha256 %s; data/release-packages.json lists "
                "%d bytes, sha256 %s. Fix the list or the release." % (fname, got_size, got_sha, size, sha))
        log("%s: %d bytes, sha256 matches the list" % (fname, size))
    if not entries:
        log("no release packages listed")


def point(root):
    entries = load(root)
    text = sys.stdin.read()
    blocks = [b.strip("\n") for b in text.split("\n\n") if b.strip()]
    out = []
    seen = set()
    for block in blocks:
        lines = block.split("\n")
        names = [line[len("Filename: "):] for line in lines if line.startswith("Filename: ")]
        if len(names) != 1:
            die("a stanza has %d Filename fields, expected 1" % len(names))
        fname = names[0][2:] if names[0].startswith("./") else names[0]
        if fname not in entries:
            die("%s is in the download directory but not listed in data/release-packages.json" % fname)
        if fname in seen:
            die("%s is indexed twice" % fname)
        seen.add(fname)
        url = entries[fname][0]
        lines = [("Filename: " + url) if line.startswith("Filename: ") else line for line in lines]
        out.append("\n".join(lines))
        log("%s: Filename -> %s" % (fname, url))
    missing = sorted(set(entries) - seen)
    if missing:
        die("listed but not indexed: %s" % ", ".join(missing))
    if out:
        sys.stdout.write("\n\n".join(out) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fetch", help="download and check the listed assets")
    f.add_argument("root", help="the project root (debs/, data/)")
    f.add_argument("dest", help="the directory the assets go to")
    p = sub.add_parser("point", help="point the Filename of each stanza at its release asset")
    p.add_argument("root", help="the project root (data/)")
    args = ap.parse_args()
    if args.command == "fetch":
        fetch(args.root, args.dest)
    else:
        point(args.root)


if __name__ == "__main__":
    main()
