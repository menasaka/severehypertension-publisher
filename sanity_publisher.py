"""
Publishes articles to severehypertension.net (Next.js + Sanity on Vercel).

Same input as wp_publisher.publish_wordpress_post: the formatted HTML body, image files,
FAQ items and categories. The HTML is converted to Sanity "Portable Text"; the FAQ goes into the
article's FAQ field (the site renders it once, with FAQPage schema); the image becomes the
featured image. Once published in Sanity, the site's webhook shows the article within seconds.

Needs SANITY_API_TOKEN (an Editor token from sanity.io/manage › API › Tokens).
"""
import html
import os
import re
import secrets
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser

import requests

import site_config as cfg
from processor import extract_yoast_description
from image_maker import IMAGE_CREDITS

API_VERSION = "v2025-02-19"

# Why the last publish failed, shown in the Streamlit app (the logs there are hard to reach).
LAST_ERROR = ""


def _fail(msg: str):
    global LAST_ERROR
    LAST_ERROR = msg
    print(msg)
    return None


def _key() -> str:
    return secrets.token_hex(6)


def _sanity():
    project = os.getenv("SANITY_PROJECT_ID", cfg.SANITY_PROJECT_ID)
    dataset = os.getenv("SANITY_DATASET", cfg.SANITY_DATASET)
    token = os.getenv("SANITY_API_TOKEN", "").strip().strip('"')
    return project, dataset, token


def sanity_configured() -> bool:
    return bool(_sanity()[2])


def _api(path: str) -> str:
    project, dataset, _ = _sanity()
    return f"https://{project}.api.sanity.io/{API_VERSION}/{path.format(dataset=dataset)}"


def _headers(extra: dict = None) -> dict:
    token = _sanity()[2]
    h = {"Authorization": f"Bearer {token}"} if token else {}
    h.update(extra or {})
    return h


def query(groq: str, params: dict = None):
    """Runs a GROQ query (published content, no CDN, so new posts show up at once)."""
    payload = {"query": groq, "params": params or {}}
    res = requests.post(_api("data/query/{dataset}") + "?perspective=published", json=payload, headers=_headers(), timeout=30)
    if res.status_code != 200:
        raise RuntimeError(f"Sanity query failed: {res.status_code} - {res.text[:300]}")
    return res.json().get("result")


# ---------------------------------------------------------------- HTML -> Portable Text

SITE_HOST_RE = re.compile(r"^https?://(?:www\.)?" + re.escape(cfg.SITE_DOMAIN) + r"(?=/|$)", re.I)


class _PortableText(HTMLParser):
    """
    Small converter for the HTML that processor.py produces: h2-h4, p, ul/ol/li,
    strong/b, em/i, u, a, br, blockquote. Anything else is read as plain text.
    """

    BLOCK_TAGS = {"p": "normal", "h2": "h2", "h3": "h3", "h4": "h4", "blockquote": "blockquote", "li": "normal"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.block = None
        self.marks = []          # active decorator / link-key stack
        self.lists = []          # "bullet" / "number"

    # --- helpers
    def _open(self, style="normal"):
        self._close()
        self.block = {"_type": "block", "_key": _key(), "style": style, "markDefs": [], "children": []}
        if self.lists:
            self.block["listItem"] = self.lists[-1]
            self.block["level"] = len(self.lists)

    def _close(self):
        b = self.block
        if b is not None:
            text = "".join(c["text"] for c in b["children"]).strip()
            if text:
                b["children"][0]["text"] = b["children"][0]["text"].lstrip()
                b["children"][-1]["text"] = b["children"][-1]["text"].rstrip()
                self.blocks.append(b)
        self.block = None

    def _text(self, text):
        if self.block is None:
            if not text.strip():
                return
            self._open()
        text = re.sub(r"\s+", " ", text)
        kids = self.block["children"]
        marks = list(self.marks)
        if kids and kids[-1]["marks"] == marks:
            kids[-1]["text"] += text
        else:
            kids.append({"_type": "span", "_key": _key(), "text": text, "marks": marks})

    # --- parser callbacks
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("ul", "ol"):
            self._close()
            self.lists.append("bullet" if tag == "ul" else "number")
        elif tag in self.BLOCK_TAGS:
            self._open(self.BLOCK_TAGS[tag])
        elif tag in ("strong", "b"):
            self.marks.append("strong")
        elif tag in ("em", "i"):
            self.marks.append("em")
        elif tag == "u":
            self.marks.append("underline")
        elif tag == "a" and a.get("href"):
            if self.block is None:
                self._open()
            href = SITE_HOST_RE.sub("", a["href"].strip()) or "/"
            mark = {"_type": "link", "_key": _key(), "href": href}
            if a.get("target") == "_blank" or href.startswith("http"):
                mark["blank"] = True
            self.block["markDefs"].append(mark)
            self.marks.append(mark["_key"])
        elif tag == "br":
            self._text("\n")

    def handle_endtag(self, tag):
        if tag in ("ul", "ol"):
            self._close()
            if self.lists:
                self.lists.pop()
        elif tag in self.BLOCK_TAGS:
            self._close()
        elif tag in ("strong", "b", "em", "i", "u"):
            want = {"strong": "strong", "b": "strong", "em": "em", "i": "em", "u": "underline"}[tag]
            for i in range(len(self.marks) - 1, -1, -1):
                if self.marks[i] == want:
                    del self.marks[i]
                    break
        elif tag == "a":
            for i in range(len(self.marks) - 1, -1, -1):
                if self.marks[i] not in ("strong", "em", "underline"):
                    del self.marks[i]
                    break

    def handle_data(self, data):
        self._text(data)


def html_to_portable_text(markup: str) -> list:
    markup = re.sub(r"<script\b[^>]*>.*?</script>", "", markup or "", flags=re.S | re.I)
    markup = re.sub(r"<!--.*?-->", "", markup, flags=re.S)
    parser = _PortableText()
    parser.feed(markup)
    parser.close()
    parser._close()
    return parser.blocks


# ---------------------------------------------------------------- helpers

def slugify(title: str) -> str:
    """Same idea as WordPress sanitize_title: lowercase ASCII words joined by hyphens."""
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9\s-]", "", s.lower())
    return re.sub(r"[\s-]+", "-", s).strip("-")[:90].rstrip("-") or "article"


# Filler words left out of article URLs, so the 4 words kept are the meaningful ones.
SLUG_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "nor", "of", "to", "in", "on", "at", "for", "with", "by", "from",
    "about", "as", "into", "is", "are", "was", "be", "can", "could", "may", "might", "should", "will", "do",
    "does", "your", "you", "my", "our", "their", "its", "it", "this", "that", "these", "those",
    "what", "why", "how", "when", "which", "who", "where", "here", "s", "vs",
}


def short_slug(title: str, max_words: int = None) -> str:
    """
    Article URL slug of at most SLUG_MAX_WORDS words (default 4): OpenAI picks the main keyword;
    if that fails, the title's first meaningful words are used (filler words dropped).
    """
    max_words = max_words or getattr(cfg, "SLUG_MAX_WORDS", 4)
    try:
        from generator import generate_slug_words
        ai_words = generate_slug_words(title, max_words)
    except Exception as e:
        print(f"Notice: slug generation unavailable ({e}); using the rule-based slug.")
        ai_words = []
    if ai_words:
        return "-".join(ai_words)
    words = [w for w in slugify(title).split("-") if w]
    keep = [w for w in words if w not in SLUG_STOP_WORDS] or words
    return "-".join(keep[:max_words]) or "article"


def unique_path(slug: str) -> str:
    """Returns /slug/ (or /slug-2/ ...) that no article or page uses yet."""
    base, n = slug, 1
    while True:
        path = f"/{slug}/"
        taken = query('count(*[_type in ["post", "page"] && path.current == $path])', {"path": path})
        if not taken:
            return path
        n += 1
        slug = f"{base}-{n}"


def category_refs(names: list) -> list:
    rows = query('*[_type == "category" && title in $names]{_id, title}', {"names": names}) or []
    by_title = {r["title"]: r["_id"] for r in rows}
    refs = [{"_type": "reference", "_ref": by_title[n], "_key": _key()} for n in names if n in by_title]
    missing = [n for n in names if n not in by_title]
    if missing:
        print(f"Notice: no Sanity category named {missing}; skipped.")
    return refs


def credit_text(credit) -> str:
    """Photo credit as one line, e.g. '"Enchanting Forest" by Jane Doe, stocksnap (CC0) https://...'."""
    if not credit:
        return ""
    if isinstance(credit, dict):
        parts = [
            f'"{credit["title"]}"' if credit.get("title") else "",
            f'by {credit["creator"]},' if credit.get("creator") else "",
            str(credit.get("source") or ""),
            f'({credit["license"]})' if credit.get("license") else "",
            str(credit.get("landing_url") or ""),
        ]
        credit = " ".join(p for p in parts if p)
    return str(credit)[:500]


def upload_image(path: str, title: str):
    """Uploads an image file to Sanity. Returns the asset _id or None."""
    if not path or not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "jpg"
    ctype = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    params = {"filename": f"{slugify(title)}.{ext}", "label": title}
    credit = credit_text(IMAGE_CREDITS.get(path))
    if credit:
        params["description"] = credit
    with open(path, "rb") as f:
        data = f.read()
    res = requests.post(_api("assets/images/{dataset}"), params=params, data=data,
                        headers=_headers({"Content-Type": ctype}), timeout=90)
    if res.status_code == 400 and "description" in params:
        # Never lose the featured image over its credit text: retry without it.
        print(f"Notice: image upload refused the credit text ({res.text[:200]}); retrying without it.")
        params.pop("description")
        res = requests.post(_api("assets/images/{dataset}"), params=params, data=data,
                            headers=_headers({"Content-Type": ctype}), timeout=90)
    if res.status_code != 200:
        print(f"⚠️ Sanity image upload failed: {res.status_code} - {res.text[:300]}")
        return None
    return res.json().get("document", {}).get("_id")


# ---------------------------------------------------------------- publish

def publish_sanity_post(
    title: str,
    content: str,
    image_paths: list = None,
    faq_items: list = None,
    category_names: list = None,
    extra_html: str = "",
    news: dict = None,
    slug: str = None,
):
    """
    Creates a published article in Sanity. Returns a dict shaped like the WordPress result
    (link, preview_url, edit_url, featured_ok, schema_in_head, ...) or None on failure.
    """
    global LAST_ERROR
    LAST_ERROR = ""
    project, dataset, token = _sanity()
    if not token:
        return _fail("❌ SANITY_API_TOKEN is not set.")
    site = os.getenv("SITE_PUBLIC_URL", cfg.SITE_URL).rstrip("/")

    try:
        path = unique_path(slug or short_slug(title))
        asset_id = None
        for p in image_paths or []:
            asset_id = upload_image(p, title)
            if asset_id:
                break

        body = html_to_portable_text(content)
        if extra_html:
            body += html_to_portable_text(extra_html)
        body += html_to_portable_text(cfg.MEDICAL_DISCLAIMER_HTML)

        metadesc = extract_yoast_description(content)
        names = list(category_names or cfg.DEFAULT_CATEGORIES)
        # Categories every new article gets (e.g. the news section), added after the chosen ones
        # so the main category (the first) stays the editor's choice.
        names += [n for n in getattr(cfg, "ALWAYS_CATEGORIES", []) if n not in names]
        doc = {
            "_id": f"post-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{secrets.token_hex(3)}",
            "_type": "post",
            "title": title,
            "path": {"_type": "slug", "current": path},
            "publishedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "author": {"_type": "reference", "_ref": cfg.SANITY_AUTHOR_ID},
            "categories": category_refs(names),
            "excerpt": metadesc,
            "body": body,
            "seo": {"_type": "seo", "title": f"{title} | {cfg.SITE_NAME}"[:70], "description": metadesc},
        }
        if asset_id:
            doc["mainImage"] = {"_type": "imageWithAlt", "alt": title, "asset": {"_type": "reference", "_ref": asset_id}}
        if faq_items:
            doc["faq"] = [
                {"_type": "faqItem", "_key": _key(), "question": str(f.get("question", "")).strip(), "answer": str(f.get("answer", "")).strip()}
                for f in faq_items if f.get("question") and f.get("answer")
            ]
        if news:
            doc["newsSource"] = {
                "headline": news.get("headline", ""),
                "publisher": news.get("source", ""),
                "url": news.get("link", ""),
            }

        res = requests.post(
            _api("data/mutate/{dataset}") + "?returnIds=true&visibility=sync",
            json={"mutations": [{"create": doc}]},
            headers=_headers(),
            timeout=45,
        )
        if res.status_code != 200:
            return _fail(f"❌ Sanity publish failed: {res.status_code} - {res.text[:500]}")

        link = f"{site}{path}"
        studio = f"{site}/studio/structure/post;{doc['_id']}"
        print(f"\n✅ Published to Sanity: {link}")
        print(f"🖼️ Featured image: {'set' if asset_id else 'NOT set'}")
        return {
            "id": doc["_id"],
            "status": "publish",
            "link": link,
            "preview_url": link,
            "edit_url": studio,
            "yoast_metadesc": metadesc,
            "yoast_saved": True,
            "featured_media_id": asset_id,
            "featured_ok": bool(asset_id),
            # The site renders the FAQ field with FAQPage JSON-LD in <head>-equivalent markup.
            "schema_in_head": bool(doc.get("faq")),
            "schema_script": "",
            "target": "sanity",
        }
    except Exception as e:
        return _fail(f"❌ Exception during Sanity publication: {e}")


def recent_posts(days: int = 10) -> list:
    """
    Recent articles in the same shape autopublish.py reads from WordPress:
    [{date_gmt, title: {rendered}, content: {rendered}}], newest first.
    Auto-published news posts carry the news marker so the daily slot count works.
    """
    rows = query(
        '*[_type == "post" && publishedAt > $after] | order(publishedAt desc)'
        '{publishedAt, title, newsSource, "text": pt::text(body)}',
        {"after": datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() - days * 86400, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
    ) or []
    out = []
    for r in rows:
        src = r.get("newsSource") or {}
        marker = f'<p class="{cfg.SOURCE_MARKER}">{html.escape(src.get("headline", ""))}</p>' if src else ""
        out.append({
            "date_gmt": (r.get("publishedAt") or "")[:19],
            "title": {"rendered": r.get("title", "")},
            "content": {"rendered": marker + html.escape(r.get("text") or "")},
        })
    return out


def check_write_access():
    """
    Checks that SANITY_API_TOKEN can create articles in this project, without writing anything
    (a Sanity dry-run mutation). Returns (ok, message).
    """
    project, dataset, token = _sanity()
    if not token:
        return False, "SANITY_API_TOKEN is not set."
    token = token.strip()
    try:
        res = requests.post(
            _api("data/mutate/{dataset}") + "?dryRun=true",
            json={"mutations": [{"createOrReplace": {"_id": "drafts.publisher-access-check", "_type": "post", "title": "Access check"}}]},
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
    except Exception as e:
        return False, f"Could not reach Sanity: {e}"
    if res.status_code == 200:
        return True, f"Sanity project `{project}`: token can publish"
    if res.status_code == 401:
        return False, f"Sanity rejected the token (401). It is wrong, revoked, or from another project (this one is `{project}`)."
    if res.status_code == 403:
        return False, "The token has no write access (403). Create an **Editor** token in sanity.io/manage → API → Tokens."
    return False, f"Sanity check failed: {res.status_code} - {res.text[:200]}"
