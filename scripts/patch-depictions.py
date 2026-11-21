#!/usr/bin/env python3
"""Add the live rating, the download count and the Rate / Report buttons to the depictions of a
built site (the _site copies, never the committed files).

For every <site>/depictions/<package id>/ it patches
  depiction.json  (Details tab): a Rating section with a DepictionRatingView (only with votes), the
                  table rows "Rating" and "Downloads", a "Source code" button (the entry's "source" in
                  data/package-repos.json, none without one) and the buttons "Rate this package" and
                  "Report an issue" (where the package's entry in data/package-repos.json says)
  index.html      the same, at the markers <!--ratings:summary-->, <!--ratings:rows--> and
                  <!--ratings:links--> (a page without a marker is left as it is, with a warning)
from the files written by fetch-ratings.py (votes) and fetch-downloads.py (downloads).

Report an issue goes to
  report "repo"      https://github.com/<package's own repo>/issues/new
  report "imod-repo" the bug-report.yml form of this repository, the package already chosen
  report "none"      no button

Usage: patch-depictions.py SITE_DIR RATINGS_JSON [--downloads DOWNLOADS_JSON]
                           [--repos data/package-repos.json] [--repo owner/name]
"""
import argparse
import html
import json
import os
import sys
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RATING_TITLE = "Rating"
DOWNLOADS_TITLE = "Downloads"
RATE_TITLE = "Rate this package"
REPORT_TITLE = "Report an issue"
SOURCE_TITLE = "Source code"
RATE_NOTE = "One vote per GitHub account; a new vote shows after the next site update (a few minutes)."
DL_NOTE = ("Downloads: GitHub release asset downloads, including direct downloads from release pages, plus the "
           "total carried over from the previous source. Downloads served by GitHub Pages are not counted.")
DL_NOTE_NO_RELEASES = ("Downloads: the total carried over from the previous source; it does not grow, "
                       "because this source cannot count downloads.")


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
    d = (entry or {}).get("total")
    if d is None:
        return None
    return "{:,}".format(int(d))


def note_text(entry, repos, pid):
    """The small print under the buttons."""
    if downloads_text(entry) is None:
        return RATE_NOTE
    has_releases = bool((repos.get(pid) or {}).get("repo"))
    return RATE_NOTE + " " + (DL_NOTE if has_releases else DL_NOTE_NO_RELEASES)


def urls(repo, pid, repos):
    """(rate url, report url or None)."""
    base = "https://github.com/%s/issues/new" % repo
    rate = "%s?template=rate-package.yml&package=%s" % (base, urllib.parse.quote(pid, safe=""))
    info = repos.get(pid) or {}
    mode = info.get("report", "none")
    if mode == "repo" and info.get("repo"):
        report = "https://github.com/%s/issues/new" % info["repo"]
    elif mode == "imod-repo":
        report = "%s?template=bug-report.yml&package=%s" % (base, urllib.parse.quote(pid, safe=""))
    else:
        report = None
    return rate, report


def source_url(pid, repos):
    """The package's open-source repository (https only), or None."""
    s = (repos.get(pid) or {}).get("source")
    return s if isinstance(s, str) and s.startswith("https://") else None


def stars(mean):
    full = max(0, min(5, int(round(mean))))
    return "★" * full + "☆" * (5 - full)


def patch_json(dep, pid, entry, dl, repo, repos):
    rate_url, report_url = urls(repo, pid, repos)
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
    dtext = downloads_text(dl)
    if dtext is not None:
        rows.append({"class": "DepictionTableTextView", "title": DOWNLOADS_TITLE, "text": dtext})
    last = max((i for i, v in enumerate(views) if v.get("class") == "DepictionTableTextView"), default=None)
    if last is None:
        views.extend(rows)
    else:
        views[last + 1:last + 1] = rows
    # 3. buttons at the end
    source = source_url(pid, repos)
    if source:  # right after the table rows, as a plain button like any hand-written source link
        at = max(i for i, v in enumerate(views) if v.get("class") == "DepictionTableTextView") + 1
        views.insert(at, {"class": "DepictionTableButtonView", "title": SOURCE_TITLE, "action": source,
                          "openExternal": 1})
    views.append({"class": "DepictionSeparatorView"})
    views.append({"class": "DepictionTableButtonView", "title": RATE_TITLE, "action": rate_url, "openExternal": 1})
    if report_url:
        views.append({"class": "DepictionTableButtonView", "title": REPORT_TITLE, "action": report_url,
                      "openExternal": 1})
    views.append({"class": "DepictionMarkdownView", "markdown": "*" + note_text(dl, repos, pid) + "*", "useSpacing": True})
    return dep


def patch_html(text, pid, entry, dl, repo, repos, where=""):
    rate_url, report_url = urls(repo, pid, repos)
    e = html.escape
    summary = ""
    if entry["count"]:
        summary = "<h2>Rating</h2><p><strong>%s</strong> %s</p>" % (stars(entry["mean"]), e(rating_text(entry)))
    rows = "<tr><td>%s</td><td>%s</td></tr>" % (e(RATING_TITLE), e(rating_text(entry)))
    dtext = downloads_text(dl)
    if dtext is not None:
        rows += "<tr><td>%s</td><td>%s</td></tr>" % (e(DOWNLOADS_TITLE), e(dtext))
    links = ""
    source = source_url(pid, repos)
    if source:
        links += '<p><a href="%s">%s</a></p>\n' % (e(source, quote=True), e(SOURCE_TITLE))
    links += '<p><a class="btn" href="%s">%s</a>' % (e(rate_url, quote=True), e(RATE_TITLE))
    if report_url:
        links += ' <a href="%s">%s</a>' % (e(report_url, quote=True), e(REPORT_TITLE))
    links += '</p><p class="mut"><em>%s</em></p>' % e(note_text(dl, repos, pid))
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
    ap.add_argument("--downloads", help="the file fetch-downloads.py wrote (without it no Downloads row)")
    ap.add_argument("--repos", default=os.path.join(ROOT, "data", "package-repos.json"))
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY") or "imod-commission/imod-repo")
    args = ap.parse_args()
    data = json.load(open(args.ratings, encoding="utf-8"))
    packages = data.get("packages") or {}
    downloads = {}
    if args.downloads:
        downloads = json.load(open(args.downloads, encoding="utf-8")).get("packages") or {}
    repos = json.load(open(args.repos, encoding="utf-8")).get("packages") or {}
    depdir = os.path.join(args.site, "depictions")
    if not os.path.isdir(depdir):
        sys.exit("error: %s not found" % depdir)
    n = 0
    for pid in sorted(os.listdir(depdir)):
        d = os.path.join(depdir, pid)
        if not os.path.isdir(d):
            continue
        if pid not in repos:
            warn("%s is not in package-repos.json: no Report an issue button" % pid)
        entry = packages.get(pid) or {"count": 0, "mean": None}
        dl = downloads.get(pid)
        jp = os.path.join(d, "depiction.json")
        if os.path.isfile(jp):
            dep = json.load(open(jp, encoding="utf-8"))
            out = json.dumps(patch_json(dep, pid, entry, dl, args.repo, repos), ensure_ascii=False, indent=2) + "\n"
            json.loads(out)  # must parse
            with open(jp, "w", encoding="utf-8") as f:
                f.write(out)
        hp = os.path.join(d, "index.html")
        if os.path.isfile(hp):
            text = open(hp, encoding="utf-8").read()
            with open(hp, "w", encoding="utf-8") as f:
                f.write(patch_html(text, pid, entry, dl, args.repo, repos, hp))
        n += 1
    print("patched %d depiction folder(s) in %s" % (n, depdir))


if __name__ == "__main__":
    main()
