#!/usr/bin/env python3
"""Add the live ratings, the download count and the rate/report links to the depictions of a
built site (the _site copies, never the committed files).

For every <site>/depictions/<package id>/ it patches
  depiction.json  (Details tab): a Rating section with a DepictionRatingView (only with votes), the
                  table rows "Rating (YouRepo votes + GitHub issue votes)" and the Downloads row,
                  and the buttons "Rate this package" and "Report an issue / comment"
  index.html      the same, at the markers <!--ratings:summary-->, <!--ratings:rows--> and
                  <!--ratings:links--> (a page without a marker is left as it is, with a warning)
from the file written by fetch-ratings.py.

Usage: patch-depictions.py SITE_DIR RATINGS_JSON [--repo owner/name]
"""
import argparse
import html
import json
import os
import sys
import urllib.parse

RATING_TITLE = "Rating (YouRepo votes + GitHub issue votes)"
RATE_TITLE = "Rate this package"
REPORT_TITLE = "Report an issue / comment"
NOTE = "One vote per GitHub account; a new vote shows after the next site update (a few minutes)."


def warn(msg):
    print("warning: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning::" + msg)


def mean_text(mean):
    return "%.1f" % mean


def rating_text(entry):
    n = entry["count"]
    if not n:
        return "No votes yet"
    return "%s (%d %s)" % (mean_text(entry["mean"]), n, "vote" if n == 1 else "votes")


def downloads_text(entry):
    d = entry.get("downloads")
    if d is None:
        return None
    t = "{:,}".format(int(d))
    if entry.get("downloadsDetail"):
        t += " (%s)" % entry["downloadsDetail"]
    return t


def urls(repo, pid):
    base = "https://github.com/%s/issues/new" % repo
    rate = "%s?template=rate-package.yml&package=%s" % (base, urllib.parse.quote(pid, safe=""))
    return rate, base


def stars(mean):
    full = max(0, min(5, int(round(mean))))
    return "★" * full + "☆" * (5 - full)


def patch_json(dep, pid, entry, label, repo):
    rate_url, report_url = urls(repo, pid)
    tab = dep["tabs"][0]
    views = tab["views"]
    # 1. Rating section before "Information"
    if entry["count"]:
        section = [
            {"class": "DepictionHeaderView", "title": "Rating"},
            {"class": "DepictionRatingView", "rating": round(entry["mean"], 2), "alignment": 1},
            {"class": "DepictionSeparatorView"},
        ]
        idx = next((i for i, v in enumerate(views)
                    if v.get("class") == "DepictionHeaderView" and v.get("title") == "Information"), None)
        if idx is None:
            views.extend(section)
        else:
            views[idx:idx] = section
    # 2. rows after the last table row of the Details tab
    rows = [{"class": "DepictionTableTextView", "title": RATING_TITLE, "text": rating_text(entry)}]
    dl = downloads_text(entry)
    if dl is not None:
        rows.append({"class": "DepictionTableTextView", "title": label, "text": dl})
    last = max((i for i, v in enumerate(views) if v.get("class") == "DepictionTableTextView"), default=None)
    if last is None:
        views.extend(rows)
    else:
        views[last + 1:last + 1] = rows
    # 3. buttons at the end
    views.append({"class": "DepictionSeparatorView"})
    views.append({"class": "DepictionTableButtonView", "title": RATE_TITLE, "action": rate_url, "openExternal": 1})
    views.append({"class": "DepictionTableButtonView", "title": REPORT_TITLE, "action": report_url,
                  "openExternal": 1})
    views.append({"class": "DepictionMarkdownView", "markdown": "*" + NOTE + "*", "useSpacing": True})
    return dep


def patch_html(text, pid, entry, label, repo, where=""):
    rate_url, report_url = urls(repo, pid)
    e = html.escape
    summary = ""
    if entry["count"]:
        summary = "<h2>Rating</h2><p><strong>%s</strong> %s</p>" % (stars(entry["mean"]), e(rating_text(entry)))
    rows = "<tr><td>%s</td><td>%s</td></tr>" % (e(RATING_TITLE), e(rating_text(entry)))
    dl = downloads_text(entry)
    if dl is not None:
        rows += "<tr><td>%s</td><td>%s</td></tr>" % (e(label), e(dl))
    links = ('<p><a class="btn" href="%s">%s</a> <a href="%s">%s</a></p><p class="mut"><em>%s</em></p>'
             % (e(rate_url, quote=True), e(RATE_TITLE), e(report_url, quote=True), e(REPORT_TITLE), e(NOTE)))
    for marker, repl in (("<!--ratings:summary-->", summary), ("<!--ratings:rows-->", rows),
                         ("<!--ratings:links-->", links)):
        if marker not in text:
            warn("%s has no %s marker" % (where or pid, marker))
            continue
        text = text.replace(marker, repl, 1)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("ratings")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY") or "imod-commission/imod-repo")
    args = ap.parse_args()
    data = json.load(open(args.ratings, encoding="utf-8"))
    label = data.get("downloadsLabel") or "Downloads"
    packages = data.get("packages") or {}
    depdir = os.path.join(args.site, "depictions")
    if not os.path.isdir(depdir):
        sys.exit("error: %s not found" % depdir)
    n = 0
    for pid in sorted(os.listdir(depdir)):
        d = os.path.join(depdir, pid)
        if not os.path.isdir(d):
            continue
        entry = packages.get(pid) or {"count": 0, "mean": None, "downloads": None}
        jp = os.path.join(d, "depiction.json")
        if os.path.isfile(jp):
            dep = json.load(open(jp, encoding="utf-8"))
            out = json.dumps(patch_json(dep, pid, entry, label, args.repo), ensure_ascii=False, indent=2) + "\n"
            json.loads(out)  # must parse
            with open(jp, "w", encoding="utf-8") as f:
                f.write(out)
        hp = os.path.join(d, "index.html")
        if os.path.isfile(hp):
            text = open(hp, encoding="utf-8").read()
            with open(hp, "w", encoding="utf-8") as f:
                f.write(patch_html(text, pid, entry, label, args.repo, hp))
        n += 1
    print("patched %d depiction folder(s) in %s" % (n, depdir))


if __name__ == "__main__":
    main()
