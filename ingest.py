import argparse
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_EXE = Path(r"C:\Users\vasek\AppData\Roaming\Python\Python314\Scripts\hdporncomics.exe")
CATALOG_PATH = Path("catalog.json")
MANGA_ROOT = Path("manga")


def run(cmd, cwd=None):
    cp = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if cp.returncode != 0:
        raise RuntimeError(f"Command failed:\n{' '.join(map(str, cmd))}\n\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}")
    return cp.stdout


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(s: str):
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "untitled"


def ensure_catalog():
    if not CATALOG_PATH.exists():
        CATALOG_PATH.write_text(json.dumps({"version": 1, "generated_at": now_iso(), "manga": []}, indent=2), encoding="utf-8")
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def save_catalog(catalog):
    catalog["generated_at"] = now_iso()
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")


def find_json_files(root: Path):
    return list(root.rglob("*.json"))


def parse_metadata_from_json_files(files):
    # Best-effort extraction across unknown schema
    # returns: manga_title, chapter_title, chapter_number
    manga_title = None
    chapter_title = None
    chapter_number = None

    def pick(d, keys):
        for k in keys:
            if isinstance(d, dict) and k in d and d[k]:
                return d[k]
        return None

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue

        # common field guesses
        mt = pick(data, ["manga_title", "series_title", "manhwa_title", "comic_title", "title"])
        ct = pick(data, ["chapter_title", "chapter", "name", "title"])
        cn = pick(data, ["chapter_number", "number", "chapter_no", "chapterIndex"])

        # if nested
        if not mt and isinstance(data, dict):
            for k in ["manga", "series", "manhwa", "comic"]:
                if isinstance(data.get(k), dict):
                    mt = mt or pick(data[k], ["title", "name"])
        if not ct and isinstance(data, dict):
            for k in ["chapter", "episode"]:
                if isinstance(data.get(k), dict):
                    ct = ct or pick(data[k], ["title", "name"])
                    cn = cn or pick(data[k], ["number", "index"])

        if mt and not manga_title:
            manga_title = str(mt).strip()
        if ct and not chapter_title:
            chapter_title = str(ct).strip()

        if cn is not None and chapter_number is None:
            try:
                chapter_number = int(float(str(cn)))
            except Exception:
                pass

    # try derive chapter number from chapter title
    if chapter_number is None and chapter_title:
        m = re.search(r"(\d+)", chapter_title)
        if m:
            chapter_number = int(m.group(1))

    return manga_title, chapter_title, chapter_number


def find_images(root: Path):
    imgs = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        imgs.extend(root.rglob(ext))
    return sorted(imgs)


def normalize_to_jpg(src: Path, dst: Path):
    # no conversion dependency: just copy and rename to .jpg
    # (works if source is jpg/jpeg; png/webp renamed but still usable in many readers)
    shutil.copy2(src, dst)


def get_or_create_manga(catalog, title):
    manga_id = slugify(title)
    for m in catalog["manga"]:
        if m["id"] == manga_id:
            return m
    m = {
        "id": manga_id,
        "title": title,
        "cover": f"manga/{manga_id}/cover.jpg",
        "info": f"manga/{manga_id}/info.json",
        "chapters": []
    }
    catalog["manga"].append(m)
    return m


def next_ch_num(manga):
    nums = []
    for ch in manga.get("chapters", []):
        try:
            nums.append(int(ch.get("number")))
        except Exception:
            pass
    return max(nums) + 1 if nums else 1


def write_pages_json(chapter_dir: Path):
    pages = [p.name for p in sorted(chapter_dir.glob("*.jpg"))]
    (chapter_dir / "pages.json").write_text(json.dumps({"pages": pages}, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="URL -> images -> manga/* -> catalog.json")
    ap.add_argument("url")
    ap.add_argument("--title", help="override manga title")
    ap.add_argument("--chapter-title", help="override chapter title")
    ap.add_argument("--chapter-number", type=int, help="override chapter number")
    ap.add_argument("--exe", default=str(DEFAULT_EXE))
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    exe = Path(args.exe)
    if not exe.exists():
        raise FileNotFoundError(f"Executable not found: {exe}")

    MANGA_ROOT.mkdir(exist_ok=True)
    catalog = ensure_catalog()

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        # 1) metadata first
        run([str(exe), "--noimages", args.url, "-d", str(tmpdir), "-f"])
        meta_files = find_json_files(tmpdir)
        meta_manga_title, meta_ch_title, meta_ch_num = parse_metadata_from_json_files(meta_files)

        manga_title = args.title or meta_manga_title
        if not manga_title:
            # fallback from URL
            last = urlparse(args.url).path.rstrip("/").split("/")[-1]
            manga_title = last.replace("-", " ") or "Unknown Manga"

        # 2) images
        run([str(exe), "--images-only", args.url, "-d", str(tmpdir), "-f"])
        imgs = find_images(tmpdir)
        if not imgs:
            raise RuntimeError("No images downloaded.")

        manga = get_or_create_manga(catalog, manga_title)
        manga_id = manga["id"]
        manga_dir = MANGA_ROOT / manga_id
        manga_dir.mkdir(parents=True, exist_ok=True)

        ch_num = args.chapter_number or meta_ch_num or next_ch_num(manga)
        ch_title = args.chapter_title or meta_ch_title or f"Chapter {ch_num}"
        ch_slug = f"ch-{int(ch_num):03}"
        ch_dir = manga_dir / ch_slug
        ch_dir.mkdir(parents=True, exist_ok=True)

        for i, src in enumerate(imgs, 1):
            dst = ch_dir / f"{i:03}.jpg"
            normalize_to_jpg(src, dst)

        write_pages_json(ch_dir)

        cover = manga_dir / "cover.jpg"
        if not cover.exists():
            first = ch_dir / "001.jpg"
            if first.exists():
                shutil.copy2(first, cover)

        info = {
            "title": manga_title,
            "source_url": args.url,
            "updated_at": now_iso()
        }
        (manga_dir / "info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")

        # upsert chapter
        ch_id = f"{manga_id}-{ch_slug}"
        existing = None
        for c in manga["chapters"]:
            if c["id"] == ch_id:
                existing = c
                break

        payload = {
            "id": ch_id,
            "number": int(ch_num),
            "title": ch_title,
            "path": f"manga/{manga_id}/{ch_slug}/",
            "uploaded_at": now_iso()
        }

        if existing:
            existing.update(payload)
        else:
            manga["chapters"].append(payload)

        manga["chapters"] = sorted(manga["chapters"], key=lambda x: x.get("number", 0))
        save_catalog(catalog)

    if args.commit or args.push:
        run(["git", "add", "catalog.json", f"manga/{manga_id}"])
    if args.commit:
        run(["git", "commit", "-m", f"Add {manga_title} {ch_title}"])
    if args.push:
        run(["git", "push", "origin", "main"])

    print(f"OK: {manga_title} / {ch_title}")


if __name__ == "__main__":
    main()