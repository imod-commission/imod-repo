#!/usr/bin/env python3
"""Point the Filename of the packages listed in data/release-filenames.json at their GitHub release
asset, in an apt-ftparchive `Packages` index (stdin), and write the index (stdout).

Each override names one package version by package id, version and architecture, and the absolute
URL of its release asset:
  {"package": "com.imodcommission.26page", "version": "1.0.0", "architecture": "iphoneos-arm64",
   "url": "https://github.com/imod-commission/26Page/releases/download/1.0/<file>.deb"}
For each override:
  1. its stanza must be in the index exactly once, with Filename debs/<file>.deb, where <file> is
     <package>_<version>_<architecture>.deb (the asset has that same name);
  2. debs/<file> must have the index's Size and SHA256 (the index describes that file);
  3. the asset is downloaded and must have the same size and SHA256 as debs/<file>;
  4. only then the stanza's Filename line becomes the URL. Size, MD5sum, SHA1, SHA256 and every other
     line are left as they are, so the hashes of the index stay valid.
Every other stanza is copied byte for byte. Any failure stops the build (exit 1, a message on stderr):
a Filename must never point at a file that is not the one in debs/. Each rewrite is logged on stderr.

Usage: override-filenames.py ROOT [--downloads-dir DIR] < Packages.raw > Packages.pointed
  ROOT is the project root (debs/, data/). --downloads-dir DIR reads DIR/<file> instead of
  downloading the asset (tests).
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request

CHUNK = 1 << 16
TIMEOUT = 120
URL_RE = re.compile(
    r"^https://github\.com/imod-commission/[A-Za-z0-9._-]+/releases/download/[^/\s]+/([^/\s]+\.deb)$")


def log(msg):
    print("release-filenames: " + msg, file=sys.stderr)


def die(msg):
    print("error: release-filenames: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::error::release-filenames: " + msg, file=sys.stderr)
    sys.exit(1)


def load_overrides(root):
    path = os.path.join(root, "data", "release-filenames.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        die("data/release-filenames.json cannot be read (%s)" % e)
    items = data.get("overrides") if isinstance(data, dict) else None
    if not isinstance(items, list):
        die('data/release-filenames.json needs an "overrides" list')
    out = []
    for n, item in enumerate(items, 1):
        try:
            pid, ver, arch, url = item["package"], item["version"], item["architecture"], item["url"]
        except (KeyError, TypeError):
            die("override %d needs package, version, architecture and url" % n)
        fname = "%s_%s_%s.deb" % (pid, ver, arch)
        m = URL_RE.match(url) if isinstance(url, str) else None
        if not m or m.group(1) != fname:
            die("%s: url must be https://github.com/imod-commission/<repo>/releases/download/<tag>/%s, got %r"
                % (fname, fname, url))
        out.append((pid, ver, arch, fname, url))
    return out


def file_size_sha256(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
            n += len(chunk)
    return n, h.hexdigest()


def asset_size_sha256(url, fname, downloads_dir):
    if downloads_dir:
        return file_size_sha256(os.path.join(downloads_dir, fname))
    # No token: the asset is public, and urllib follows GitHub's redirect to the file itself.
    req = urllib.request.Request(url, headers={"User-Agent": "imod-repo-release-filenames"})
    h = hashlib.sha256()
    n = 0
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            h.update(chunk)
            n += len(chunk)
    return n, h.hexdigest()


def value_of(lines, key):
    prefix = key + ": "
    return [line[len(prefix):] for line in lines if line.startswith(prefix)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("root", help="the project root (debs/, data/)")
    ap.add_argument("--downloads-dir", help="read the assets from DIR/<file> instead of downloading (tests)")
    args = ap.parse_args()

    overrides = load_overrides(args.root)
    text = sys.stdin.read()
    # apt-ftparchive puts one blank line between stanzas; split and join give back the same bytes.
    blocks = text.split("\n\n")
    fields = [b.split("\n") for b in blocks]
    for pid, ver, arch, fname, url in overrides:
        label = "%s %s %s" % (pid, ver, arch)
        hits = [i for i, lines in enumerate(fields)
                if value_of(lines, "Package") == [pid]
                and value_of(lines, "Version") == [ver]
                and value_of(lines, "Architecture") == [arch]]
        if len(hits) != 1:
            die("%s: %d entries in the index, expected exactly 1" % (label, len(hits)))
        i = hits[0]
        lines = fields[i]
        if value_of(lines, "Filename") != ["debs/" + fname]:
            die("%s: Filename is %s, expected debs/%s" % (label, value_of(lines, "Filename"), fname))
        path = os.path.join(args.root, "debs", fname)
        if not os.path.isfile(path):
            die("%s: debs/%s is missing" % (label, fname))
        size, sha = file_size_sha256(path)
        if value_of(lines, "Size") != [str(size)] or value_of(lines, "SHA256") != [sha]:
            die("%s: the index's Size or SHA256 is not the one of debs/%s (%d bytes, sha256 %s); "
                "rebuild the index" % (label, fname, size, sha))
        try:
            got_size, got_sha = asset_size_sha256(url, fname, args.downloads_dir)
        except Exception as e:
            die("%s: cannot read the release asset %s (%s: %s)" % (label, url, type(e).__name__, e))
        if (got_size, got_sha) != (size, sha):
            die("%s: the release asset is not the file in debs/. Asset: %d bytes, sha256 %s. "
                "debs/%s: %d bytes, sha256 %s. Filename left as debs/%s; fix the asset or the override."
                % (label, got_size, got_sha, fname, size, sha, fname))
        lines = [("Filename: " + url) if line.startswith("Filename: ") else line for line in lines]
        fields[i] = lines
        blocks[i] = "\n".join(lines)
        log("%s: Filename debs/%s -> %s (%d bytes, sha256 matches debs/)" % (label, fname, url, size))
    sys.stdout.write("\n\n".join(blocks))
    log("%d entr%s pointed at release assets" % (len(overrides), "y" if len(overrides) == 1 else "ies"))


if __name__ == "__main__":
    main()
