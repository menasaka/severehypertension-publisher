"""
Command-line version of the pipeline (no Streamlit).

    python main.py "Your Post Title"          -> one post
    python main.py                            -> every title in GOOGLE_SHEET_ID
Posts are always published live.
"""
import io
import os
import sys
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

import site_config as cfg
from generator import generate_article_content, generate_faqs
from processor import process_and_format_article
from image_maker import create_unique_images
from publisher import publish_post

POST_STATUS = "publish"


def run_automation_pipeline(topic_title: str):
    print(f"\n🚀 {topic_title}")
    raw_content = generate_article_content(topic_title)
    faq_items = generate_faqs(topic_title)
    print(f"   Article: {len(raw_content.split())} words, {len(faq_items)} FAQs")

    formatted = process_and_format_article(raw_content)
    image_paths = create_unique_images(topic_title)

    post = publish_post(
        title=topic_title,
        content=formatted,
        image_paths=image_paths,
        faq_items=faq_items,
        category_names=list(cfg.DEFAULT_CATEGORIES),
        status=POST_STATUS,
    )
    if post:
        print(f"   ✅ {post.get('link')} - {post.get('edit_url')}")
    else:
        print("   ⚠️ Failed to create post")
    return post


def process_sheet_queue(sheet_id: str):
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    resp = requests.get(csv_url, timeout=15)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    titles = [t for t in df.iloc[:, 0].dropna().astype(str).str.strip()
              if t and t.lower() not in ["title", "titles", "topic", "topics"]]
    print(f"✅ Found {len(titles)} title(s)")
    for i, title in enumerate(titles, start=1):
        run_automation_pipeline(title)
        if i < len(titles):
            time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_automation_pipeline(" ".join(sys.argv[1:]))
    elif os.getenv("GOOGLE_SHEET_ID"):
        process_sheet_queue(os.getenv("GOOGLE_SHEET_ID"))
    else:
        print("Pass a title, or set GOOGLE_SHEET_ID.")
