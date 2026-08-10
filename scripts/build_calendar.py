#!/usr/bin/env python3
"""Count commits per day and write them to data/commits.json.

The page used to ask the API for this on every visit. That cost a dozen
requests against an allowance of sixty an hour shared by everyone behind the
same address, so a couple of reloads — or one busy university network — left
the grid empty. Here the counting happens once, in the workflow, with a token
that allows five thousand an hour, and the page reads a file.

Every owned repository is counted, not a sample of them, and the answer is
the same for every visitor.
"""

import io
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

USER = "mavroul1s"
DAYS = 371                     # 53 weeks, the width of the grid
PAGES = 10                     # per repository; 1000 commits in a year is plenty
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "commits.json")


def log(msg):
    print(msg, flush=True)


def api(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "%s-calendar" % USER,
    })
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    since = (datetime.utcnow() - timedelta(days=DAYS)).replace(
        hour=0, minute=0, second=0, microsecond=0)
    since_iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        repos = api("https://api.github.com/users/%s/repos"
                    "?per_page=100&type=owner&sort=pushed" % USER)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        log("the repository list could not be read (%s) — leaving the file alone" % e)
        return 0

    if not isinstance(repos, list) or not repos:
        log("no repositories came back — leaving the file alone")
        return 0

    days = {}
    counted = 0
    for repo in repos:
        full = repo["full_name"]
        total = 0
        for page in range(1, PAGES + 1):
            url = ("https://api.github.com/repos/%s/commits"
                   "?since=%s&per_page=100&page=%d" % (full, since_iso, page))
            try:
                commits = api(url)
            except urllib.error.HTTPError as e:
                # 409 is an empty repository, which is not a failure
                if e.code != 409:
                    log("  %-46s %s" % (full, e))
                commits = []
            except (urllib.error.URLError, ValueError) as e:
                log("  %-46s %s" % (full, e))
                commits = []
            if not commits:
                break
            for c in commits:
                stamp = (c.get("commit") or {}).get("author") or \
                        (c.get("commit") or {}).get("committer") or {}
                when = stamp.get("date")
                if not when:
                    continue
                key = when[:10]
                days[key] = days.get(key, 0) + 1
                total += 1
            if len(commits) < 100:
                break
        counted += 1
        if total:
            log("  %-46s %4d" % (full, total))

    if not days:
        log("no commits found in the window — leaving the file alone")
        return 0

    # drop anything that fell outside the window the grid can show
    first = (date.today() - timedelta(days=DAYS)).isoformat()
    days = {k: v for k, v in days.items() if k >= first}

    payload = {
        "generated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "since": since_iso[:10],
        "repos": counted,
        "total": sum(days.values()),
        "days": dict(sorted(days.items())),
    }

    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))

    old = None
    try:
        with io.open(OUT, encoding="utf-8") as f:
            old = json.load(f)
    except (IOError, ValueError):
        pass
    if old and old.get("days") == payload["days"]:
        log("commits.json: unchanged (%d commits over %d repositories)"
            % (payload["total"], counted))
        return 0

    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    log("commits.json: %d commits on %d days over %d repositories"
        % (payload["total"], len(days), counted))
    return 0


if __name__ == "__main__":
    sys.exit(main())
