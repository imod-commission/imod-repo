#!/usr/bin/env python3
"""Thank and close the rating issues that fetch-ratings.py counted.

Reads the JSON written by fetch-ratings.py (its "closeable" list: valid rating issues that are
still open) and, for each one, posts a short thank-you comment and closes the issue as completed.
The votes were counted before this runs, and closed issues still count, so closing changes nothing
in the numbers; it keeps this repository's issue list for the issues that need a person.

Safe to run again: only issues that are open are touched, and only the numbers in the list. A
failure (no token, no permission, network) only warns; the exit code stays 0 so the deploy goes on.
The workflow needs `issues: write` for it. Events made with the workflow's own GITHUB_TOKEN do not
start another workflow run, so closing does not loop.

Standard library only. Usage:
  close-rating-issues.py ratings.json [--repo owner/name] [--api URL] [--dry-run]
GITHUB_TOKEN authenticates; GITHUB_REPOSITORY is the default --repo.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def warn(msg):
    print("warning: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning::" + msg)


def message(item):
    stars = "%d star%s" % (item["rating"], "" if item["rating"] == 1 else "s")
    who = "@" + item["login"] + " " if item.get("login") else ""
    if item.get("counted", True):
        return ("Thanks %sfor rating `%s`: your %s vote is counted and shows on the package page "
                "after the next site update (a few minutes).\n\n"
                "This issue is closed automatically; ratings are closed once counted. To change your "
                "vote, submit a new rating for the same package: your newest one replaces the older."
                % (who, item["package"], stars))
    return ("Thanks %sfor rating `%s`. A newer rating from you for this package replaces this %s "
            "vote, so this one is not counted any more.\n\nThis issue is closed automatically."
            % (who, item["package"], stars))


def call(api, method, path, token, payload=None):
    req = urllib.request.Request(
        api.rstrip("/") + path,
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "imod-repo-close-ratings",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8") or "null")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ratings")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY") or "imod-commission/imod-repo")
    ap.add_argument("--api", default="https://api.github.com")
    ap.add_argument("--dry-run", action="store_true", help="print what would be done")
    args = ap.parse_args()

    items = json.load(open(args.ratings, encoding="utf-8")).get("closeable") or []
    if not items:
        print("close-rating-issues: nothing to close")
        return
    token = os.environ.get("GITHUB_TOKEN")
    if not token and not args.dry_run:
        warn("no GITHUB_TOKEN: the %d counted rating issue(s) stay open" % len(items))
        return
    done = 0
    for item in items:
        n = item["number"]
        if args.dry_run:
            print("would close #%s (%s, %s): %s" % (n, item["package"], item["rating"],
                                                    message(item).split("\n")[0]))
            continue
        try:
            call(args.api, "POST", "/repos/%s/issues/%s/comments" % (args.repo, n), token,
                 {"body": message(item)})
            call(args.api, "PATCH", "/repos/%s/issues/%s" % (args.repo, n), token,
                 {"state": "closed", "state_reason": "completed"})
            done += 1
        except (urllib.error.URLError, OSError, ValueError, TimeoutError) as e:
            warn("could not close rating issue #%s (%s)" % (n, e))
    print("close-rating-issues: closed %d of %d" % (done, len(items)))


if __name__ == "__main__":
    main()
