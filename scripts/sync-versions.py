#!/usr/bin/env python3
"""Make the version each depiction shows match the newest version of its package in the Packages index.

The index's Version is the one in each .deb's control file, the same version a release ships. For every
depiction folder DEPICTIONS_DIR/<package id>/ whose package the index lists, the version is written in
  depiction.json  the "Version" row of the Details tab
  index.html      the version after the package id in the header, and the "Version" row of the table
A package the index does not list is left as it is, and so is a file already the same. Changelog titles
are written by hand and are not touched. A file without the Version row or line is reported and kept.

Run by scripts/update-repository.sh on the copies in _site (every build), and by hand on the committed
depictions/ folder, with an index made from debs/.

Usage: sync-versions.py PACKAGES_FILE DEPICTIONS_DIR
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys


def warn(msg):
    print("warning: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning::" + msg)


def newer(a, b):
    """True when version a is later than b (dpkg's own ordering)."""
    return subprocess.run(["dpkg", "--compare-versions", a, "gt", b]).returncode == 0


def newest_versions(path):
    """{package id: newest Version} of an index (stanzas of Package and Version fields)."""
    newest = {}
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    for block in text.split("\n\n"):
        fields = {}
        for line in block.split("\n"):
            if ":" in line and line[:1] not in (" ", "\t"):
                k, v = line.split(":", 1)
                fields.setdefault(k.strip(), v.strip())
        pid, ver = fields.get("Package"), fields.get("Version")
        if not pid or not ver:
            continue
        if pid not in newest or newer(ver, newest[pid]):
            newest[pid] = ver
    return newest


def sync_json(path, version):
    """True when the file changed; a string names the problem."""
    dep = json.load(open(path, encoding="utf-8"))
    rows = 0
    changed = False
    for tab in dep.get("tabs", []):
        for v in tab.get("views", []):
            if v.get("class") == "DepictionTableTextView" and v.get("title") == "Version":
                rows += 1
                if v.get("text") != version:
                    v["text"] = version
                    changed = True
    if not rows:
        return "no Version row"
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(dep, ensure_ascii=False, indent=2) + "\n")
    return changed


def sync_html(path, pid, version):
    """True when the file changed; a string names the problem."""
    text = open(path, encoding="utf-8").read()
    v = html.escape(version)
    new, n_head = re.subn('(<div class="mut">' + re.escape(pid) + ' \u00b7 )[^<]*(</div>)',
                          lambda m: m.group(1) + v + m.group(2), text, count=1)
    new, n_row = re.subn(r'(<tr><td>Version</td><td>)[^<]*(</td></tr>)',
                         lambda m: m.group(1) + v + m.group(2), new, count=1)
    if not n_head and not n_row:
        return "no Version line"
    if new == text:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def sync_root(path, newest):
    """Set the version in each root-page row (<a href="depictions/<id>/">) to the newest in the index.

    True when the file changed; a string names the problem. A row whose package the index does not list
    is left as it is.
    """
    text = open(path, encoding="utf-8").read()
    new = text
    rows = 0
    for pid, version in newest.items():
        pat = re.compile(r'(<a href="depictions/' + re.escape(pid) +
                         r'/">[^\n]*?<strong>[^<]*</strong> <span class="mut">)([^<\n]*?)( \u00b7 )')
        new, n = pat.subn(lambda m, v=version: m.group(1) + html.escape(v) + m.group(3), new, count=1)
        rows += n
    if not rows:
        return "no version row"
    if new == text:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("packages")
    ap.add_argument("depictions")
    args = ap.parse_args()
    newest = newest_versions(args.packages)
    changed = 0
    for pid in sorted(os.listdir(args.depictions)):
        d = os.path.join(args.depictions, pid)
        version = newest.get(pid)
        if not os.path.isdir(d) or version is None:
            continue
        results = []
        jp = os.path.join(d, "depiction.json")
        if os.path.isfile(jp):
            results.append(sync_json(jp, version))
        hp = os.path.join(d, "index.html")
        if os.path.isfile(hp):
            results.append(sync_html(hp, pid, version))
        for r in results:
            if isinstance(r, str):
                warn("%s: %s" % (pid, r))
            elif r:
                changed += 1
    # The source's own page (index.html beside depictions/) lists every tweak with its version too.
    root = os.path.join(os.path.dirname(os.path.abspath(args.depictions)), "index.html")
    if os.path.isfile(root):
        r = sync_root(root, newest)
        if isinstance(r, str):
            warn("index.html: %s" % r)
        elif r:
            changed += 1
    print("set the version of %d file(s) in %s" % (changed, args.depictions))


if __name__ == "__main__":
    sys.exit(main())
