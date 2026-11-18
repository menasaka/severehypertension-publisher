import os
import io
import time
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Bridge Streamlit Cloud secrets into environment variables (before other modules read them)
try:
    for k, v in st.secrets.items():
        if isinstance(v, str):
            os.environ[k] = v
except Exception:
    pass

import site_config as cfg
from generator import generate_article_content, generate_faqs
from processor import process_and_format_article
from image_maker import create_unique_images
from publisher import publish_post

st.set_page_config(
    page_title=f"SEO Blog Publisher | {cfg.SITE_NAME}",
    page_icon=cfg.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 800; color: #18345C; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1rem; color: #64748B; margin-bottom: 1.5rem; }
    .status-badge { display: inline-block; padding: 4px 12px; background-color: #E6F4F5; color: #1F6F7A;
                    border-radius: 9999px; font-size: 0.85rem; font-weight: 600; margin-right: 8px; }
    .success-card { background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 20px; margin: 15px 0; }
</style>
""", unsafe_allow_html=True)


def get_env_status():
    return {
        "has_openai": bool(os.getenv("OPENAI_API_KEY")),
        "has_sanity": bool(os.getenv("SANITY_API_TOKEN")),
    }


def category_picker(label: str, key: str):
    names = st.multiselect(
        label,
        options=list(cfg.CATEGORY_MAP.keys()),
        default=cfg.DEFAULT_CATEGORIES,
        key=key,
        help="Select one or more categories. The first one is the main category.",
    )
    return names or cfg.DEFAULT_CATEGORIES


def run_pipeline(title: str, category_names, report=None):
    def step(msg, pct):
        if report:
            report(msg, pct)

    step("🧠 [1/5] Writing the article with OpenAI...", 15)
    raw_content = generate_article_content(title)

    step(f"❓ [2/5] Article drafted ({len(raw_content.split())} words). Writing 12 FAQs...", 35)
    faq_items = generate_faqs(title)

    step("⚙️ [3/5] Formatting headings, bolding keywords, adding internal links...", 55)
    formatted = process_and_format_article(raw_content)

    step("🎨 [4/5] Creating the featured image...", 75)
    images = create_unique_images(title)

    step("🚀 [5/5] Uploading the image and publishing the article...", 90)
    post = publish_post(
        title=title,
        content=formatted,
        image_paths=images,
        faq_items=faq_items,
        category_names=category_names,
    )
    return post, raw_content, formatted, faq_items


@st.cache_data(ttl=300, show_spinner=False)
def sanity_access(token_fingerprint: str):
    """
    Whether the Sanity token can publish (dry run, nothing is written). Cached per token, so a new
    token in Secrets is checked at once; the same token is re-checked every 5 minutes.
    """
    from sanity_publisher import check_write_access
    return check_write_access()


def token_fingerprint() -> str:
    """Start, end and length of the token in use, enough to compare with the one you pasted."""
    from sanity_publisher import _sanity
    t = _sanity()[2]
    return f"{t[:6]}…{t[-4:]} ({len(t)} characters)" if len(t) > 12 else f"({len(t)} characters)"


def main():
    # Password gate
    app_password = os.getenv("APP_PASSWORD", "")
    if app_password:
        entered = st.text_input("🔑 Enter Access Password", type="password")
        if not entered:
            st.warning("🔒 Please enter the access password to use this application.")
            st.stop()
        elif entered != app_password:
            st.error("❌ Incorrect password. Access denied.")
            st.stop()

    env = get_env_status()

    with st.sidebar:
        st.header("⚙️ System Status")
        if os.getenv("PIXABAY_API_KEY", "").strip() or os.getenv("PEXELS_API_KEY", "").strip():
            st.success("Photos: Pixabay/Pexels connected")
        else:
            st.error("PIXABAY_API_KEY missing: articles get fewer topic photos (add it in Secrets)")
        if env["has_sanity"]:
            fp = token_fingerprint()
            ok, msg = sanity_access(fp)
            (st.success if ok else st.error)(msg)
            st.caption(f"Token in use: `{fp}`")
        else:
            st.error("SANITY_API_TOKEN missing (add it in Secrets)")
        if env["has_openai"]:
            st.success(f"OpenAI API: Connected ({os.getenv('OPENAI_MODEL', cfg.DEFAULT_OPENAI_MODEL)})")
        else:
            st.error("OPENAI_API_KEY missing")

        st.divider()
        st.subheader("🛠️ Publishing Parameters")
        st.markdown("""
        - **Target Word Count:** ~1,200+ words
        - **Headings:** Question-based `H2`
        - **Density:** 3–4 paragraphs per H2
        - **Internal Links:** 3–4 severehypertension.net pages
        - **SEO:** Title + meta description
        - **FAQ:** 12 Q&A in the article's FAQ field (site adds FAQPage schema)
        - **Medical disclaimer:** added to every post
        - **Featured image:** 1 per post
        """)

    st.markdown(f'<div class="main-header">{cfg.PAGE_ICON} {cfg.SITE_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Automated SEO Article Generator & Publishing Pipeline for severehypertension.net</div>', unsafe_allow_html=True)
    st.markdown(
        '<div>'
        '<span class="status-badge">OpenAI</span>'
        '<span class="status-badge">Featured Image Engine</span>'
        '<span class="status-badge">Sanity</span>'
        '<span class="status-badge">SEO & FAQ Schema</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    tab_single, tab_batch = st.tabs(["📝 Single Post Generator", "📊 Google Sheets Batch Queue"])

    with tab_single:
        st.subheader("Generate & Publish Single Article")
        st.caption("Quick Select Sample Topics:")
        cols = st.columns(len(cfg.SAMPLE_TOPICS))
        for idx, topic in enumerate(cfg.SAMPLE_TOPICS):
            if cols[idx].button(f"Topic {idx + 1}", key=f"topic_btn_{idx}", help=topic):
                st.session_state["blog_title"] = topic

        title_input = st.text_input(
            "Blog Post Title",
            value=st.session_state.get("blog_title", cfg.SAMPLE_TOPICS[0]),
            placeholder="Enter exact blog post title...",
        )
        category_names = category_picker("📁 Categories", "single_cats")

        if st.button("🚀 Generate & Publish Live", type="primary", use_container_width=True):
            if not title_input.strip():
                st.warning("Please enter a valid blog post title.")
                return

            progress_bar = st.progress(0)
            status_box = st.empty()

            def report(msg, pct):
                status_box.info(msg)
                progress_bar.progress(pct)

            try:
                post_data, raw_content, formatted, faq_items = run_pipeline(
                    title_input, category_names, report
                )
                progress_bar.progress(100)

                if not post_data:
                    from sanity_publisher import LAST_ERROR
                    status_box.error(f"Failed to publish the article. {LAST_ERROR or 'Check the logs and credentials.'}")
                    return
                editor_name = "Sanity Studio"

                status_box.empty()
                post_id = post_data.get("id")
                edit_url = post_data["edit_url"]
                preview_url = post_data.get("preview_url", "")
                label = "Published LIVE" if post_data.get("status") == "publish" else f"saved as {post_data.get('status', '').upper()}"

                st.markdown(f"""
                <div class="success-card">
                    <h3 style="color: #15803D; margin-top: 0;">🎉 Blog Post {label}!</h3>
                    <p><strong>Post ID:</strong> {post_id} | <strong>Categories:</strong> {', '.join(category_names)}</p>
                    <p><strong>Edit URL:</strong> <a href="{edit_url}" target="_blank">{edit_url}</a></p>
                    <p><strong>Article URL:</strong> <a href="{preview_url}" target="_blank">{preview_url}</a></p>
                </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                c1.link_button(f"📝 Open in {editor_name}", edit_url, use_container_width=True)
                c2.link_button("🌐 Open Article", preview_url, use_container_width=True)
                st.divider()
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Article Words", len(raw_content.split()))
                m2.metric("FAQs", len(faq_items))
                m3.metric("Status", str(post_data.get("status", "")).upper())
                m4.metric("Featured Image", "✅ Set" if post_data.get("featured_ok") else "❌ Missing")
                if not post_data.get("featured_ok"):
                    st.warning("The featured image was not set. Check the app logs (Manage app → logs) for the error.")

                with st.expander("🔍 SEO & Meta Details", expanded=True):
                    st.markdown(f"**SEO Title:** `{title_input} | {cfg.SITE_NAME}`")
                    st.markdown("**Meta Description:**")
                    st.info(post_data.get("yoast_metadesc", ""))

                if post_data.get("schema_in_head"):
                    st.success("✅ FAQ saved to the article's FAQ section (the site adds the FAQPage schema).")
                else:
                    st.warning("No FAQ was saved with this article.")

                with st.expander("❓ FAQ"):
                    for idx, item in enumerate(faq_items, 1):
                        st.markdown(f"**{idx}. {item.get('question')}**")
                        st.write(item.get('answer'))

                with st.expander("📄 Full HTML Body Content"):
                    st.code(formatted, language="html")

            except Exception as ex:
                status_box.error(f"❌ An error occurred during pipeline execution: {ex}")
                st.exception(ex)

    with tab_batch:
        st.subheader("Batch Publish from Google Sheet")
        st.markdown("Titles in column A of a sheet shared as **Anyone with the link can view**. Posts run one after another with a short cooldown.")

        b1, b2 = st.columns([2, 1])
        with b1:
            sheet_id_input = st.text_input("Google Sheet ID", value=os.getenv("GOOGLE_SHEET_ID", ""))
        with b2:
            batch_names = category_picker("Batch Categories", "batch_cats")

        if st.button("📥 Load Sheet & Start Batch", type="secondary"):
            if not sheet_id_input.strip():
                st.warning("Enter a Google Sheet ID first.")
                return
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id_input.strip()}/export?format=csv"
            try:
                resp = requests.get(csv_url, timeout=15)
                if resp.status_code != 200:
                    st.error(f"Could not load Google Sheet (HTTP {resp.status_code}). Check the sharing setting.")
                    return

                df = pd.read_csv(io.StringIO(resp.text))
                raw_titles = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
                titles = [t for t in raw_titles if t and t.lower() not in ["title", "titles", "topic", "topics"]]
                st.success(f"Found {len(titles)} titles in queue!")

                batch_progress = st.progress(0)
                batch_box = st.empty()
                for idx, topic in enumerate(titles, start=1):
                    batch_box.info(f"Processing ({idx}/{len(titles)}): **{topic}**...")
                    try:
                        post, *_ = run_pipeline(topic, batch_names)
                    except Exception as e:
                        post = None
                        st.write(f"⚠️ Error on '{topic}': {e}")
                    if post:
                        st.write(f"✅ **[{idx}/{len(titles)}] Published LIVE:** {topic} — [View]({post.get('preview_url', '')}) · [Edit]({post.get('edit_url', '')})")
                    else:
                        st.write(f"⚠️ **[{idx}/{len(titles)}] Failed:** {topic}")
                    batch_progress.progress(int(idx / len(titles) * 100))
                    if idx < len(titles):
                        time.sleep(5)

                batch_box.success("🏁 All batch titles processed!")
            except Exception as e:
                st.error(f"Error processing sheet: {e}")


if __name__ == "__main__":
    main()
