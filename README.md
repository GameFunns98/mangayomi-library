# mangayomi-library

GitHub-hosted manga library for Mangayomi sync.

## Structure

```text
catalog.json
extension/mylibrary.js
manga/<manga-id>/
  cover.jpg
  info.json
  ch-001/001.jpg ...
```

## Requirements (Windows)

- Python 3.14+
- `hdporncomics` installed
- `git` installed and authenticated

## Install scraper

```bat
py -m pip install --user hdporncomics
```

From your logs, executable is at:

`C:\Users\vasek\AppData\Roaming\Python\Python314\Scripts\hdporncomics.exe`

## Import chapter from URL

```bat
py ingest.py "https://example/chapter-url" --title "Solo Leveling" --chapter-title "Chapter 1" --commit --push
```

## Notes

- Use only content you are allowed to redistribute (e.g. CC0).
- `catalog.json` is updated automatically by `ingest.py`.
- First page of first imported chapter is used as `cover.jpg` if missing.