#!/usr/bin/env python3
"""Keep the news log in step with the public repository list.

Run from a scheduled workflow. It compares GitHub's answer against the
snapshot in data/repos.json and edits index.html between the NEWS markers:

    a repository appears   -> an entry is added, dated when it was created
    a repository is gone   -> every entry tied to it is removed
    a repository is renamed-> an entry is added, dated today

Repositories are tracked by numeric id, not by name, because the id survives
a rename and the name does not — that is what makes a rename distinguishable
from a delete followed by a create.

Only <li> elements inside the markers are touched, and manual entries are
left exactly as written; the script never invents a date and never rewrites
prose it did not author. Standard library only.
"""

import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

USER = "mavroul1s"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "index.html")
SNAP = os.path.join(ROOT, "data", "repos.json")
START, END = "<!-- NEWS:START -->", "<!-- NEWS:END -->"

# A run that would delete more than this many entries is treated as a bad
# answer from the API rather than a real deletion, and changes nothing.
MAX_REMOVALS = 3

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def log(msg):
    print(msg, flush=True)


def ordinal(day):
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return "%02d%s" % (day, suffix)


def pretty(iso):
    """2026-08-05 -> (Aug 05th, '26)"""
    y, m, d = int(iso[0:4]), int(iso[5:7]), int(iso[8:10])
    return "(%s %s, '%02d)" % (MONTHS[m - 1], ordinal(d), y % 100)


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def fetch_repos():
    url = ("https://api.github.com/users/%s/repos"
           "?per_page=100&type=owner&sort=created" % USER)
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "%s-news-sync" % USER,
    })
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load_snapshot():
    try:
        with io.open(SNAP, encoding="utf-8") as f:
            return {str(k): v for k, v in json.load(f).items()}
    except (IOError, ValueError):
        return {}


def entry_html(repo):
    """One <li>, in the same shape a hand-written entry takes."""
    created = repo["created_at"][:10]
    desc = (repo.get("description") or "").strip().rstrip(".")
    what = "New repository opened: %s" % repo["name"]
    if desc:
        what += " — %s" % desc
    return (
        '        <li data-repo="%d" data-auto="1">\n'
        '          <time datetime="%s">%s</time>\n'
        '          <a class="what" href="%s" target="_blank" rel="noopener">%s</a>\n'
        '        </li>' % (repo["id"], created, pretty(created),
                           esc(repo["html_url"]), esc(what))
    )


def rename_html(repo, old_name, today):
    what = "%s renamed to %s" % (old_name, repo["name"])
    return (
        '        <li data-repo="%d" data-auto="1">\n'
        '          <time datetime="%s">%s</time>\n'
        '          <a class="what" href="%s" target="_blank" rel="noopener">%s</a>\n'
        '        </li>' % (repo["id"], today, pretty(today),
                           esc(repo["html_url"]), esc(what))
    )


def split_entries(block):
    return re.findall(r"[ \t]*<li\b.*?</li>", block, flags=re.S)


def entry_id(li):
    m = re.search(r'data-repo="(\d+)"', li)
    return m.group(1) if m else None


def entry_date(li):
    m = re.search(r'datetime="([^"]+)"', li)
    return m.group(1) if m else "0000"


def main():
    if not os.path.exists(PAGE):
        log("no index.html at %s" % PAGE)
        return 1

    try:
        listing = fetch_repos()
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        log("the API could not be read (%s) — leaving the log alone" % e)
        return 0

    if not isinstance(listing, list) or not listing:
        log("the API returned no repositories — refusing to treat that as a "
            "clean sweep, leaving the log alone")
        return 0

    now = {str(r["id"]): r for r in listing}
    snap = load_snapshot()
    today = os.environ.get("NEWS_TODAY") or \
        __import__("datetime").date.today().isoformat()

    fresh = [] if not snap else [i for i in now if i not in snap]
    gone = [i for i in snap if i not in now]
    renamed = [(i, snap[i]["name"], now[i]["name"]) for i in now
               if i in snap and snap[i]["name"] != now[i]["name"]]

    if not snap:
        log("no snapshot yet — recording %d repositories without announcing "
            "any of them" % len(now))

    html = io.open(PAGE, encoding="utf-8").read()
    a, b = html.index(START) + len(START), html.index(END)
    entries = split_entries(html[a:b])
    before = len(entries)

    removals = [li for li in entries if entry_id(li) in gone]
    if len(removals) > MAX_REMOVALS:
        log("%d entries would be removed in one run, which looks like a bad "
            "answer rather than %d deleted repositories — stopping"
            % (len(removals), len(gone)))
        return 0

    for rid in gone:
        log("gone:    %s (%s)" % (snap[rid]["name"], rid))
    entries = [li for li in entries if entry_id(li) not in gone]

    added = []
    for rid in fresh:
        log("new:     %s (%s)" % (now[rid]["name"], rid))
        added.append(entry_html(now[rid]))
    for rid, old, new in renamed:
        log("renamed: %s -> %s (%s)" % (old, new, rid))
        added.append(rename_html(now[rid], old, today))

    entries = added + entries
    # newest first; stable, so hand-written order survives within a date
    entries.sort(key=entry_date, reverse=True)

    block = "\n" + "\n".join(entries) + "\n      "
    out = html[:a] + block + html[b:]

    changed = out != html
    if changed:
        io.open(PAGE, "w", encoding="utf-8", newline="").write(out)
        log("index.html: %d entries -> %d" % (before, len(entries)))
    else:
        log("index.html: nothing to change")

    if not os.path.isdir(os.path.dirname(SNAP)):
        os.makedirs(os.path.dirname(SNAP))
    record = {rid: {"name": r["name"], "created_at": r["created_at"][:10]}
              for rid, r in sorted(now.items(), key=lambda kv: -int(kv[0]))}
    io.open(SNAP, "w", encoding="utf-8", newline="").write(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
