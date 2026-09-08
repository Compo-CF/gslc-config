# GSLC app configuration

Live settings for the Good Shepherd companion app. The app reads
`config.json` at launch, so the values below can change **without building or
releasing a new version of the app**.

Everything here is already public on the church's own website.

## Editing

Edit `config.json` and commit. Phones pick it up on their next launch —
GitHub's CDN caches for about five minutes, so allow a few minutes before
checking on a device.

| Field | Why it matters |
|---|---|
| `service.bibleStudy`, `service.worship` | Shown on the home screen and New Here. Wrong times send people at the wrong hour — this is the highest-risk value in the file. |
| `links.giving` | The Give button. If the church leaves Vanco, change it here. |
| `contact.*` | Tap-to-call, tap-to-email and directions. |
| `feeds.sermons`, `feeds.weekly` | Where the app reads sermons and the weekly email. Only change if the site moves or the Mailchimp list is rebuilt. |

## Rules

- **Keep it valid JSON.** The app ignores a malformed file and falls back to
  the last good copy, then to the values compiled into it — so a mistake is
  never fatal, but it does mean an edit can silently fail to apply. Paste the
  file into a JSON validator if you're unsure.
- **Don't rename or remove keys.** A missing key falls back to the compiled
  default. Renaming one is the same as deleting it.
- `schema` is for future changes to the file's shape. Leave it alone.

## The Sunday Bible study

`bible-study.json` is different from everything else here. Every other feed
the app reads is something the church already publishes; this one is written
by hand, ahead of time, and nothing appears in the app's **Study** tab until
someone writes it.

The file holds the standing details once, then one entry per class:

```json
{
  "title": "Sunday Bible Study",
  "time": "",
  "location": "Fellowship Hall",
  "intro": "One or two sentences about the class.",
  "classes": [
    {
      "date": "2026-09-13",
      "topic": "What the class is on",
      "reading": "John 1:1-14",
      "summary": "A sentence or two of orientation.",
      "notes": [
        "One paragraph per entry.",
        "What will be covered, questions to think about, anything worth reading beforehand."
      ]
    }
  ]
}
```

| Field | Notes |
|---|---|
| `time` | Leave **empty** unless the class meets at a different hour from `service.bibleStudy` in `config.json`. Empty means the app uses that one, so the time is only ever written down once. |
| `location`, `intro` | Optional. Each is simply left out of the screen when empty. |
| `date` | `YYYY-MM-DD`, the Sunday the class meets. Required. |
| `topic` | Required. Everything else is optional. |
| `reading`, `summary`, `notes` | The lesson itself. A class with none of these still shows on the schedule as a date and a topic — it just isn't tappable. |

### How the app uses it

The next class on or after today is expanded at the top of the tab; later
ones are listed under **Coming Up**; past ones fold away under **Earlier
Classes**. So classes can be added weeks ahead — nothing is shown early
except its date and topic, and nothing has to be deleted afterwards.

An entry missing `date` or `topic` is dropped rather than shown blank, and
the whole file falls back to the last good copy on the phone if an edit
breaks the JSON. With no classes at all the tab says lessons are posted
before each Sunday, which is the correct thing for it to say.