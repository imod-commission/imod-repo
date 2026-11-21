#!/usr/bin/env python3
"""Post-process an apt-ftparchive `Packages` index (stdin) and write the result (stdout).

For every package that has a folder depictions/<Package>/ it sets
  Depiction      <site>/depictions/<id>/            (when index.html exists)
  SileoDepiction <site>/depictions/<id>/depiction.json (when depiction.json exists)
  Icon           <site>/depictions/<id>/icon.png    (when icon.png exists)
so the old .deb files, which are never rebuilt, can still carry a depiction.

It also fills what an old deb lacks, without ever failing on it:
  Name        <- last part of the package id
  Maintainer  <- Author, Author <- Maintainer
  Section     <- Tweaks (with a warning on stderr)

Usage: inject-metadata.py SITE_URL DEPICTIONS_DIR < Packages.raw > Packages
"""
import os
import sys


def parse(text):
    stanzas = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        block = block.strip("\n")
        if not block.strip():
            continue
        fields = []  # [name, value] keeping order; continuation lines stay in the value
        for line in block.split("\n"):
            if line[:1] in (" ", "\t") and fields:
                fields[-1][1] += "\n" + line
            elif ":" in line:
                k, v = line.split(":", 1)
                fields.append([k, v.lstrip(" ")])
        stanzas.append(fields)
    return stanzas


def get(fields, key):
    for k, v in fields:
        if k.lower() == key.lower():
            return v
    return None


def put(fields, key, value):
    for f in fields:
        if f[0].lower() == key.lower():
            f[1] = value
            return
    fields.append([key, value])


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    site = sys.argv[1].rstrip("/")
    depdir = sys.argv[2]
    stanzas = parse(sys.stdin.read())
    if not stanzas:
        sys.exit("error: no package in the index")
    for fields in stanzas:
        pid = get(fields, "Package")
        fn = get(fields, "Filename") or "?"
        if not pid:
            sys.exit("error: a stanza without Package (%s)" % fn)
        for need in ("Version", "Architecture", "Filename"):
            if not get(fields, need):
                sys.exit("error: %s has no %s" % (fn, need))
        if not get(fields, "Name"):
            put(fields, "Name", pid.rsplit(".", 1)[-1])
        a, m = get(fields, "Author"), get(fields, "Maintainer")
        if not m and a:
            put(fields, "Maintainer", a)
        if not a and m:
            put(fields, "Author", m)
        if not get(fields, "Section"):
            print("warning: %s has no Section, using Tweaks" % fn, file=sys.stderr)
            put(fields, "Section", "Tweaks")
        d = os.path.join(depdir, pid)
        base = "%s/depictions/%s" % (site, pid)
        if os.path.isfile(os.path.join(d, "index.html")):
            put(fields, "Depiction", base + "/")
        if os.path.isfile(os.path.join(d, "depiction.json")):
            put(fields, "SileoDepiction", base + "/depiction.json")
        if os.path.isfile(os.path.join(d, "icon.png")):
            put(fields, "Icon", base + "/icon.png")
    out = []
    for fields in stanzas:
        out.append("\n".join("%s: %s" % (k, v) for k, v in fields))
    sys.stdout.write("\n\n".join(out) + "\n\n")


if __name__ == "__main__":
    main()
