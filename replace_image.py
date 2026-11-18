"""
Gives existing articles a new featured photo (same photo search as new articles:
Pixabay -> Pexels -> Openverse, topic-specific phrases, never a photo already used on the site).

Usage:
    python replace_image.py /how-to-lower-your-blood-pressure/              # replace this article's image
    python replace_image.py --title-cards                       # every article whose image is a title card
    python replace_image.py /how-to-lower-your-blood-pressure/ --dry-run    # find a photo, don't change the article
    python replace_image.py --check "Low Blood Sugar Symptoms"  # only test which photo source works

The article is changed only when a real photo is found (never replaced by another title card).
Also runs on GitHub: Actions -> "Replace featured image" -> Run workflow.
"""
import argparse
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

from autopublish import load_combined_secret  # noqa: E402  (also reads the AUTOMATION secret)

load_combined_secret()

import image_maker  # noqa: E402
import sanity_publisher as sp  # noqa: E402


def find_photo(title: str):
    """Returns (local path, credit) for a real photo, or (None, None)."""
    photo, credit = image_maker.find_topic_photo(title)
    if photo is None:
        return None, None
    font = image_maker.ensure_font_exists()
    img = image_maker._photo_with_title_bar(photo, title, font)
    path = f"{image_maker._slug(title)}-photo.jpg"
    img.save(path, "JPEG", quality=88)
    image_maker.IMAGE_CREDITS[path] = credit
    return path, credit


def replace(doc: dict, dry_run: bool) -> bool:
    title, path = doc["title"], doc["path"]
    print(f"\n== {title}  ({path})")
    local, credit = find_photo(title)
    if not local:
        print("   No photo found (needs PIXABAY_API_KEY). Article left unchanged.")
        return False
    print(f"   Photo: {credit.get('source')} - {credit.get('title')} - {credit.get('landing_url')}")
    if dry_run:
        image_maker.cleanup_local_images([local])
        return True
    asset_id = sp.upload_image(local, title)
    image_maker.cleanup_local_images([local])
    if not asset_id:
        print("   Upload failed. Article left unchanged.")
        return False
    res = requests.post(
        sp._api("data/mutate/{dataset}") + "?visibility=sync",
        json={"mutations": [{"patch": {"id": doc["_id"], "set": {
            "mainImage": {"_type": "imageWithAlt", "alt": title, "asset": {"_type": "reference", "_ref": asset_id}},
        }}}]},
        headers=sp._headers(),
        timeout=45,
    )
    if res.status_code != 200:
        print(f"   Sanity update failed: {res.status_code} {res.text[:300]}")
        return False
    print(f"   Done: {sp.cfg.SITE_URL}{path}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="article URL paths, e.g. /how-to-lower-your-blood-pressure/")
    ap.add_argument("--title-cards", action="store_true", help="all articles whose featured image is a title card")
    ap.add_argument("--check", metavar="TITLE", help="only test the photo search for this title")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.check:
        local, credit = find_photo(args.check)
        print(f"\nPhoto source: {credit.get('source') if credit else 'NONE (a title card would be used)'}")
        image_maker.cleanup_local_images([local])
        return 0 if local else 1

    if not sp.sanity_configured():
        print("SANITY_API_TOKEN is not set.")
        return 1

    docs = []
    if args.title_cards:
        docs += sp.query('*[_type == "post" && mainImage.asset->description == "branded title card"]'
                         '{_id, title, "path": path.current}') or []
    for p in args.paths:
        p = "/" + p.strip("/") + "/"
        d = sp.query('*[_type == "post" && path.current == $p][0]{_id, title, "path": path.current}', {"p": p})
        if d:
            docs.append(d)
        else:
            print(f"No article at {p}")
    if not docs:
        print("Nothing to do.")
        return 0
    ok = sum(replace(d, args.dry_run) for d in docs)
    print(f"\n{ok} of {len(docs)} article(s) {'would get' if args.dry_run else 'got'} a new photo.")
    return 0 if ok == len(docs) else 1


if __name__ == "__main__":
    sys.exit(main())
