#!/usr/bin/env python3
"""Combine the carried-over old votes with the votes cast as GitHub issues.

Reads
  * data/yourepo-baseline.json   the old votes (per package id), the starting values
  * the issues of the repository labelled "rating" (GitHub REST API), open AND closed, made with the
    issue form .github/ISSUE_TEMPLATE/rate-package.yml

and writes a small JSON file (never committed; the site build reads it) with, per package id,
the combined vote count and mean, and a list of the valid rating issues that are still open
("closeable"), which scripts/close-rating-issues.py thanks and closes after the count.

Rules for the issue votes
  * pull requests are skipped; so is any issue also labelled "ignore" (how a bad vote is removed)
  * the form body is read from its "### Package" and "### Rating" sections: only a package id found
    in debs/ and a rating of 1-5 are valid
  * one account = one vote per package: only the newest valid rating of an issue author counts
  * total votes = baseline votes + issue votes; mean = weighted mean of both
  * closed issues count too (the workflow closes each valid vote after counting it)

If the API cannot be read, only the baseline is used, a warning is printed and the exit code is
still 0: the deploy must not fail for it.

Standard library only. Usage:
  fetch-ratings.py --out ratings.json [--repo owner/name] [--issues-file fake.json]
                   [--baseline data/yourepo-baseline.json] [--debs debs]
GITHUB_TOKEN (optional) authenticates the API calls; GITHUB_REPOSITORY is the default --repo.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RATING_LABEL = "rating"
IGNORE_LABEL = "ignore"
MAX_PAGES = 100  # 100 issues per page
RATING_RE = re.compile(r"([1-5])(?:\s*stars?)?", re.IGNORECASE)


def warn(msg):
    print("warning: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning::" + msg)


def known_packages(debs_dir):
    """Package ids of debs/<id>_<version>_<arch>.deb (a Debian package id has no underscore)."""
    ids = set()
    for name in os.listdir(debs_dir):
        if name.endswith(".deb") and "_" in name:
            ids.add(name.split("_", 1)[0])
    return ids


def template_package_options(path):
    """The options of the `package` dropdown in the issue form (crude read, used for a warning)."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(r"^\s*id:\s*package\s*$(.*?)^\s*validations:", text, re.S | re.M)
    if not m:
        return None
    return set(re.findall(r"^\s+-\s+(\S+)\s*$", m.group(1), re.M))


def parse_sections(body):
    """{'package': ..., 'rating': ..., 'comment': ...} from '### Heading' sections.
    The first section with a heading wins, so a comment cannot forge an earlier field."""
    sections = {}
    cur, buf = None, []

    def flush():
        if cur is not None and cur not in sections:
            sections[cur] = "\n".join(buf).strip()

    for line in (body or "").replace("\r\n", "\n").split("\n"):
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            flush()
            cur, buf = m.group(1).strip().lower(), []
        elif cur is not None:
            buf.append(line)
    flush()
    return sections


def extract_vote(issue, known):
    """(author, package, rating, (created_at, number)) of a valid rating issue, else None."""
    if issue.get("pull_request") is not None:
        return None
    labels = {(l.get("name") if isinstance(l, dict) else str(l)) for l in issue.get("labels") or []}
    labels = {str(x).lower() for x in labels if x}
    if RATING_LABEL not in labels or IGNORE_LABEL in labels:
        return None
    user = issue.get("user") or {}
    author = user.get("id") if user.get("id") is not None else (user.get("login") or "").lower()
    if author in (None, ""):
        return None
    sec = parse_sections(issue.get("body"))
    package = (sec.get("package") or "").strip()
    if package not in known:
        return None
    m = RATING_RE.fullmatch((sec.get("rating") or "").strip())
    if not m:
        return None
    return author, package, int(m.group(1)), (issue.get("created_at") or "", issue.get("number") or 0)


def issue_votes(issues, known):
    """({package: [ratings]}, [valid vote issues]): one (the newest valid) rating per author and
    package is counted. The second list has every valid vote, newest or not, as
    {number, state, login, package, rating, counted}; counted is False for a vote that a newer one
    of the same author and package replaced."""
    newest = {}  # (author, package) -> (order, rating)
    valid = []
    for issue in issues:
        v = extract_vote(issue, known)
        if v is None:
            continue
        author, package, rating, order = v
        key = (author, package)
        if key not in newest or order > newest[key][0]:
            newest[key] = (order, rating)
        valid.append({
            "number": issue.get("number"),
            "state": issue.get("state") or "open",
            "login": (issue.get("user") or {}).get("login") or "",
            "package": package,
            "rating": rating,
            "order": order,
            "key": key,
        })
    for item in valid:
        item["counted"] = newest[item.pop("key")][0] == item.pop("order")
    out = {}
    for (author, package), (order, rating) in newest.items():
        out.setdefault(package, []).append(rating)
    valid.sort(key=lambda i: i["number"] or 0)
    return out, valid


def fetch_issues(repo, token):
    """All issues labelled "rating", open and closed, paginated."""
    issues = []
    for page in range(1, MAX_PAGES + 1):
        url = ("https://api.github.com/repos/%s/issues?state=all&labels=%s&per_page=100&page=%d"
               % (repo, RATING_LABEL, page))
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "imod-repo-fetch-ratings",
        })
        if token:
            req.add_header("Authorization", "Bearer " + token)
        with urllib.request.urlopen(req, timeout=30) as resp:
            chunk = json.loads(resp.read().decode("utf-8"))
        if not isinstance(chunk, list):
            raise ValueError("unexpected API answer: %r" % (chunk,))
        issues.extend(chunk)
        if len(chunk) < 100:
            break
    return issues


def combine(baseline, known, votes):
    packages = {}
    for pid in sorted(known):
        b = baseline.get(pid) or {}
        bc = int(b.get("ratingCount") or 0)
        bm = b.get("ratingMean")
        if bm is None:
            bc = 0
        ratings = votes.get(pid, [])
        ic = len(ratings)
        total = bc + ic
        mean = None
        if total:
            mean = ((bc * float(bm) if bc else 0.0) + sum(ratings)) / total
        packages[pid] = {
            "count": total,
            "mean": None if mean is None else round(mean, 4),
            "baselineCount": bc,
            "issueCount": ic,
        }
    return packages


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--baseline", default=os.path.join(ROOT, "data", "yourepo-baseline.json"))
    ap.add_argument("--debs", default=os.path.join(ROOT, "debs"))
    ap.add_argument("--template", default=os.path.join(ROOT, ".github", "ISSUE_TEMPLATE", "rate-package.yml"))
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY") or "imod-commission/imod-repo")
    ap.add_argument("--issues-file", help="read the issues from this JSON file instead of the API (tests)")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    base = json.load(open(args.baseline, encoding="utf-8"))
    baseline = base.get("packages") or {}
    known = known_packages(args.debs)
    if not known:
        sys.exit("error: no .deb in %s" % args.debs)
    opts = template_package_options(args.template)
    if opts is not None and opts != known:
        warn("the package list of %s differs from debs/ (only in form: %s; only in debs: %s)" % (
            os.path.basename(args.template), sorted(opts - known), sorted(known - opts)))

    api_ok = True
    issues = []
    try:
        if args.issues_file:
            issues = json.load(open(args.issues_file, encoding="utf-8"))
        else:
            issues = fetch_issues(args.repo, os.environ.get("GITHUB_TOKEN"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as e:
        api_ok = False
        issues = []
        warn("could not read the rating issues (%s); using the carried-over votes only" % e)

    votes, valid = issue_votes(issues, known)
    result = {
        "apiOk": api_ok,
        "packages": combine(baseline, known, votes),
        # valid vote issues still open: the workflow thanks and closes them after this count
        "closeable": [v for v in valid if v["state"] == "open"] if api_ok else [],
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out == "-":
        sys.stdout.write(text)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        n_issue = sum(len(v) for v in votes.values())
        print("ratings: %d package(s), %d issue vote(s), API %s -> %s" % (
            len(result["packages"]), n_issue, "ok" if api_ok else "FAILED (carried-over votes only)", args.out))


if __name__ == "__main__":
    main()
