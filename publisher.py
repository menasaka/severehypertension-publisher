"""
One entry point for publishing. severehypertension.net runs on Next.js + Sanity (Vercel),
so every article goes to Sanity (the old WordPress site is retired).
"""
from image_maker import cleanup_local_images


def publish_target() -> str:
    return "sanity"


def publish_post(
    title: str,
    content: str,
    image_paths: list = None,
    faq_items: list = None,
    category_names: list = None,
    status: str = "publish",
    extra_html: str = "",
    news: dict = None,
):
    """Publishes the article to Sanity. Returns the result dict, or None on failure."""
    from sanity_publisher import publish_sanity_post
    try:
        return publish_sanity_post(
            title=title, content=content, image_paths=image_paths, faq_items=faq_items,
            category_names=category_names, extra_html=extra_html, news=news,
        )
    finally:
        cleanup_local_images(image_paths)
