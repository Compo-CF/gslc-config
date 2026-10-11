"""Keep the Bible study *dates* current from the church's weekly email.

The app's Bible Study tab reads `classes[]` from this file. Those entries hold
two different kinds of thing:

  * **The schedule** — which days a class meets, and which series it belongs
    to. The church publishes this every Friday in the weekly email, including
    cancellations ("No Midweek Bible Study").
  * **The lesson** — the topic, the reading, the summary. Pastor writes these
    and they appear nowhere else. Not in the email, not on the website.

Only the first kind can be automated, and this does exactly that much. Every
class it adds carries a placeholder topic and no summary, which is how the app
renders "a date on the schedule with nothing written yet" and how the daily
monitor in gslc-app tells a written lesson from an unwritten one.

Three rules it does not break:

  * **It never edits an entry that already exists.** A lesson Pastor has
    written is never touched, reworded or reordered.
  * **It never sets `updated`.** The app prints that as "Lessons updated
    <date>", and adding a date is not updating a lesson. Claiming otherwise
    would invert the whole point of this script.
  * **It removes a date only when the email cancels it and nothing has been
    written for it.** A cancelled class with a written lesson is left alone
    and reported, because that is a person's call, not a script's.
"""

import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta
from html import unescape
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"
STUDY = HERE / "bible-study.json"

# What the app shows for a class on the schedule whose lesson is not written.
# It must be non-empty: the model drops a class with a blank topic rather than
# render a blank row, so "unwritten" has to be said out loud.
PENDING = "To be announced"

WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6}


def text_of(html):
    """The email as lines of plain text, in reading order."""
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    t = unescape(re.sub(r"<[^>]+>", "\n", t))
    out = []
    for line in (l.strip() for l in t.splitlines()):
        if line and (not out or out[-1] != line):
            out.append(line)                        # collapse repeats
    return out


def next_weekday(on_or_after, weekday):
    return on_or_after + timedelta(days=(weekday - on_or_after.weekday()) % 7)


def schedule(lines, published):
    """Dates the email says a study meets, and dates it says it does not.

    Only the "This Week" block is read, and only as far as "Announcements".
    The same words appear again lower down in the standing series blurbs
    ("Sunday School and Bible Study", "Wednesday Bible Study:"), and reading
    those as schedule would book a class every week forever.
    """
    try:
        start = next(i for i, l in enumerate(lines) if l.lower() == "this week")
    except StopIteration:
        return {}, {}

    meets, cancelled = {}, {}
    current, following = None, False

    for line in lines[start + 1:]:
        low = line.lower().rstrip(":")
        if low.startswith("announcement"):
            break
        if low in ("next sunday", "next week"):
            following, current = True, WEEKDAYS["sunday"]
            continue

        # A bare weekday is a heading. A range ("Monday - Wednesday") heads a
        # multi-day event, never a class, so taking its first day is harmless.
        head = re.match(r"^([A-Za-z]+)(?:\s*[-–]\s*[A-Za-z]+)?$", line)
        if head and head.group(1).lower() in WEEKDAYS:
            current = WEEKDAYS[head.group(1).lower()]
            continue

        if current is None or "bible study" not in low:
            continue

        day = next_weekday(published, current)
        if following:
            day += timedelta(days=7)
        # "No Midweek Bible Study" is the church saying a class is off, and it
        # is the only reason a scheduled date should ever be withdrawn.
        (cancelled if low.startswith("no ") else meets)[day.isoformat()] = line

    return meets, cancelled


def series_for(study, weekday_name):
    """The series meeting on this weekday, identified by its own `when` line."""
    for s in study.get("series", []):
        if s.get("when", "").strip().lower().startswith(weekday_name.lower()):
            # Classes carry the short name: "Set Apart", not the full title.
            return s.get("title", "").split(":")[0].strip()
    return ""


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    study = json.loads(STUDY.read_text(encoding="utf-8"))
    feed = (cfg.get("feeds") or {}).get("weekly")
    if not feed:
        print("no weekly feed in config.json; nothing to do")
        return 0

    req = urllib.request.Request(feed, headers={"User-Agent": "gslc-config"})
    with urllib.request.urlopen(req, timeout=60) as r:
        rss = ElementTree.fromstring(r.read())

    items = rss.findall(".//item")
    if not items:
        print("the archive feed carried no campaigns")
        return 0

    newest = items[0]
    published = datetime.strptime(
        newest.findtext("pubDate", "").strip()[:16], "%a, %d %b %Y").date()
    body = newest.findtext(
        "{http://purl.org/rss/1.0/modules/content/}encoded") or ""

    meets, cancelled = schedule(text_of(body), published)
    print(f"newsletter {published} — meets {sorted(meets)}, "
          f"cancelled {sorted(cancelled)}")

    classes = study.setdefault("classes", [])
    have = {c.get("date"): c for c in classes}
    added, dropped, kept = [], [], []

    for day in sorted(meets):
        if day in have:
            continue                                  # never edit what exists
        weekday = datetime.strptime(day, "%Y-%m-%d").strftime("%A")
        classes.append({
            "date": day,
            "topic": PENDING,
            "reading": "",
            "series": series_for(study, weekday),
            "summary": "",
            "notes": [],
        })
        added.append(day)

    for day in sorted(cancelled):
        existing = have.get(day)
        if not existing:
            continue
        if existing.get("summary") or existing.get("notes"):
            kept.append(day)        # written, then cancelled: a person decides
        else:
            classes.remove(existing)
            dropped.append(day)

    classes.sort(key=lambda c: c.get("date", ""))

    if kept:
        print(f"WARNING cancelled but already written, left alone: "
              f"{', '.join(kept)}")
    if not (added or dropped):
        print("schedule already current")
        return 0

    # `updated` is deliberately untouched: the app prints it as "Lessons
    # updated <date>", and nothing here writes a lesson.
    # ensure_ascii matches how the file is already written. Turning it off
    # renders every curly quote as a literal, which rewrites a dozen lines of
    # Pastor's prose nothing asked to change — a diff that reads as an edit to
    # the very content this script promises never to touch.
    STUDY.write_text(json.dumps(study, indent=2, ensure_ascii=True) + "\n",
                     encoding="utf-8")
    if added:
        print(f"added {len(added)}: {', '.join(added)}")
    if dropped:
        print(f"removed (cancelled, nothing written): {', '.join(dropped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
