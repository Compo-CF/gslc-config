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
