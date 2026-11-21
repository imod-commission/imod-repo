#!/usr/bin/env python3
"""Check that every local href/src of <site>/index.html and <site>/depictions/*/index.html points to
a file (or a folder with an index.html) in the built site. External links (http, sileo, mailto...) and
fragments are ignored.

Usage: check-site-links.py SITE_DIR      exits 1 and lists the broken ones, 0 when all resolve.
"""
import os
import re
import sys
import urllib.parse
from html.parser import HTMLParser


class Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("href", "src") and v:
                self.refs.append(v)


def check(page, site):
    p = Refs()
    p.feed(open(page, encoding="utf-8").read())
    bad = []
    for ref in p.refs:
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", ref) or ref.startswith(("#", "//")):
            continue
        path = urllib.parse.unquote(urllib.parse.urlparse(ref).path)
        if not path:
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(page), path))
        if not target.startswith(os.path.normpath(site)):
            bad.append((page, ref, "outside the site"))
            continue
        if path.endswith("/") or os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.isfile(target):
            bad.append((page, ref, "missing"))
    return bad, len(p.refs)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    site = os.path.abspath(sys.argv[1])
    pages = [os.path.join(site, "index.html")]
    dep = os.path.join(site, "depictions")
    if os.path.isdir(dep):
        pages += [os.path.join(dep, d, "index.html") for d in sorted(os.listdir(dep))
                  if os.path.isfile(os.path.join(dep, d, "index.html"))]
    bad, total = [], 0
    for page in pages:
        if not os.path.isfile(page):
            bad.append((page, "", "page missing"))
            continue
        b, n = check(page, site)
        bad += b
        total += n
    for page, ref, why in bad:
        print("broken link in %s: %s (%s)" % (os.path.relpath(page, site), ref, why), file=sys.stderr)
    print("checked %d page(s), %d reference(s), %d broken" % (len(pages), total, len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
