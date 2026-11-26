#!/usr/bin/env python3
"""Make the Description of each open-source tweak's depiction match its control file.

For every package in data/package-repos.json that has a GitHub repository ("repo"), the Description
field of that repository's `control` file (branch main, read from raw.githubusercontent.com) is written
into the depiction in DEPICTIONS_DIR/<package id>/:
  depiction.json  the markdown under the "Description" header of the Details tab
  index.html      the text between <h2>Description</h2> and the ratings marker (or the next <h2>)
Packages without a repository (no open source) are left as they are. A file already the same is not
rewritten. A control file that cannot be read, or whose Package is not this id, keeps the text the
depiction has and prints a warning; the build never fails on it. The "." lines of a control
description are paragraph breaks, and lines starting with "- " become a list.

Run by scripts/update-repository.sh on the copies in _site (every build), and by hand on the
committed depictions/ folder to keep those files in step.

Usage: sync-descriptions.py DEPICTIONS_DIR [--repos data/package-repos.json] [--branch main]
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = "https://raw.githubusercontent.com/%s/%s/control"
DESC_RE = re.compile(r"<h2>Description</h2>(.*?)(?=<!--ratings:summary-->|<h2>|</body>)", re.S)


def warn(msg):
    print("warning: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning::" + msg)


def fetch_control(repo, branch):
    req = urllib.request.Request(RAW % (repo, branch), headers={"User-Agent": "imod-repo"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def control_fields(text):
    """(Package, Description lines) of a control file. Description lines: the first line, then the
    continuation lines with a leading space; "." is an empty line (a paragraph break)."""
    package, desc = None, None
    for line in text.replace("\r\n", "\n").split("\n"):
        if desc is not None and line[:1] in (" ", "\t"):
            s = line.strip()
            desc.append("" if s == "." else s)
            continue
        if desc is not None:
            break
        if line.startswith("Package:"):
            package = line[len("Package:"):].strip()
        elif line.startswith("Description:"):
            desc = [line[len("Description:"):].strip()]
    return package, desc


def paragraphs(lines):
    """Groups of non-empty lines, split at the empty ones."""
    out, cur = [], []
    for line in lines:
        if line.strip():
            cur.append(line.strip())
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def to_markdown(lines):
    return "\n\n".join("\n".join(p) for p in paragraphs(lines))


def to_html(lines):
    blocks = []  # (kind, [items]); kind "p", "ul" or "sep"
    for para in paragraphs(lines):
        if blocks:
            blocks.append(("sep", []))
        for line in para:
            if line.startswith("- "):
                if blocks and blocks[-1][0] == "ul":
                    blocks[-1][1].append(line[2:])
                else:
                    blocks.append(("ul", [line[2:]]))
            else:
                if blocks and blocks[-1][0] == "p":
                    blocks[-1][1].append(line)
                else:
                    blocks.append(("p", [line]))
    out = []
    for kind, items in blocks:
        if kind == "p":
            out.append("<p>%s</p>" % html.escape(" ".join(items)))
        elif kind == "ul":
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % html.escape(i) for i in items))
    return "".join(out)


def sync_json(path, md):
    """True when the file changed; a string names the problem."""
    dep = json.load(open(path, encoding="utf-8"))
    views = dep["tabs"][0]["views"]
    for i, v in enumerate(views):
        if v.get("class") == "DepictionHeaderView" and v.get("title") == "Description":
            nxt = views[i + 1] if i + 1 < len(views) else {}
            if nxt.get("class") != "DepictionMarkdownView":
                return "no markdown under the Description header"
            if nxt.get("markdown") == md:
                return False
            nxt["markdown"] = md
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(dep, ensure_ascii=False, indent=2) + "\n")
            return True
    return "no Description header"


def sync_html(path, body):
    text = open(path, encoding="utf-8").read()
    m = DESC_RE.search(text)
    if not m:
        return "no Description section"
    if m.group(1).strip() == body:
        return False
    new = text[:m.start()] + "<h2>Description</h2>" + body + "\n" + text[m.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("depictions")
    ap.add_argument("--repos", default=os.path.join(ROOT, "data", "package-repos.json"))
    ap.add_argument("--branch", default="main")
    args = ap.parse_args()
    packages = json.load(open(args.repos, encoding="utf-8")).get("packages") or {}
    changed = 0
    for pid in sorted(packages):
        repo = (packages[pid] or {}).get("repo")
        d = os.path.join(args.depictions, pid)
        if not repo or not os.path.isdir(d):
            continue
        try:
            package, lines = control_fields(fetch_control(repo, args.branch))
        except Exception as e:  # network, HTTP or decoding: keep what the depiction has
            warn("%s: could not read the control file of %s (%s); its Description is kept" % (pid, repo, e))
            continue
        if package != pid:
            warn("%s: the control file of %s names %r; its Description is kept" % (pid, repo, package))
            continue
        if not lines or not any(x.strip() for x in lines):
            warn("%s: the control file of %s has no Description; kept" % (pid, repo))
            continue
        results = []
        jp = os.path.join(d, "depiction.json")
        if os.path.isfile(jp):
            results.append(sync_json(jp, to_markdown(lines)))
        hp = os.path.join(d, "index.html")
        if os.path.isfile(hp):
            results.append(sync_html(hp, to_html(lines)))
        for r in results:
            if isinstance(r, str):
                warn("%s: %s" % (pid, r))
            elif r:
                changed += 1
    print("synced the Description of %d file(s) in %s" % (changed, args.depictions))


if __name__ == "__main__":
    main()
