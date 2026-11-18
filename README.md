# 🩺 Severe Hypertension – SEO Article Publisher & Daily News Autopilot

Writes 1,200+ word high blood pressure articles with OpenAI and publishes them straight to
**https://severehypertension.net** (Next.js + Sanity on Vercel, Sanity project `epwrfm14`), with a
featured image, a page-specific FAQ (the site adds the FAQPage schema), internal links, SEO title and
meta description, and a medical disclaimer.

Cloned from `urologytoday-publisher` (the Sanity-only version) on 2026-11-18; only `site_config.py`
and a few site-name strings differ.

| | |
|---|---|
| Sanity | project `epwrfm14`, dataset `production`, author `author-david` ("Severe Hypertension Network", as on WordPress) |
| Topic rules | readings and AHA/ACC categories, home monitoring, causes, symptoms, hypertensive crisis, DASH/salt/lifestyle, medicines in general terms; AHA / ACC / CDC / NHLBI guidance; no dosing; never "stop your medicine"; no cure claims; every "when to see a doctor" section covers 180/120 with symptoms = 911 |
| News search | `hypertension OR "high blood pressure" OR "blood pressure"`; OpenAI drops market-size/business reports, non-medical "pressure", crime, animal health |
| News category | Severe Hypertension News (manual articles default to High Blood Pressure Guide) |
| Photos | Pixabay → Pexels → Openverse; BP monitors, doctors, healthy food; navy-to-crimson title card |

**All site-specific settings are in `site_config.py`.** Category names must match the Sanity category
titles exactly (for example "Severe Hypertension News", "Diet For High Blood Pressure", "High Blood Pressure Guide").

## What an article looks like in Sanity

- `title`, `path` = `/<slug>/`: at most 4 words: OpenAI picks the main keyword, else the first meaningful title words (`SLUG_MAX_WORDS`, `SLUG_PROMPT` in site_config.py); `-2` added if taken, `publishedAt` = now, author `author-david`
- `categories`: the chosen Sanity categories (first = main category)
- `body`: the article as Portable Text, then the news source line (news posts) and the disclaimer
- `faq`: 12 questions about this article only, `mainImage`: the featured photo, `excerpt` + `seo`: meta description
- `newsSource` (news posts): headline, publisher and URL of the story it is based on (read-only field in the Studio). It is also how the
  autopilot counts today's news posts and avoids covering the same headline twice.

New articles appear on the site at once (pages render on demand). The home page, category pages and
sitemap refresh through the Sanity webhook → `https://severehypertension.net/api/revalidate/`.

## Daily news autopilot (GitHub Actions)

`autopublish.py` + `.github/workflows/autopublish.yml` publish two articles a day:

| Time (California) | What happens |
|---|---|
| **9:00 am** | Newest blood pressure headline from Google News (last 24h, else 3 days) → article published |
| **2:00 pm** | Next newest headline not yet covered → article published |

The workflow runs hourly (`23 0,1,16-23 * * *` UTC). Each run publishes whichever slot is due but not
done yet, so a late or skipped GitHub run is made up by the next one until 5:59pm. A slot never posts
twice, even if re-run.

**Setup (once):** GitHub repo → Settings → Secrets and variables → Actions → New repository secret:
`OPENAI_API_KEY`, `SANITY_API_TOKEN` and `PIXABAY_API_KEY` (optional: `PEXELS_API_KEY`) (or one secret named `AUTOMATION` with lines like
`OPENAI_API_KEY = "..."`).

**Test / run now:** repo → Actions → "Daily news auto-publish" → Run workflow →
tick `dry_run` to see which headline it would pick, or set `slot` = 1 to publish one now.

**Replace a featured image:** repo → Actions → "Replace featured image" → Run workflow with the article path(s),
e.g. `/how-to-lower-your-blood-pressure/` (`replace_image.py`).

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then fill in the values
streamlit run app.py
python autopublish.py --dry-run
python main.py "How to Measure Your Blood Pressure Correctly at Home"
```

## Streamlit Community Cloud

App → Settings → **Secrets**: paste `.streamlit/secrets.toml.example` with real values
(`OPENAI_API_KEY`, `SANITY_API_TOKEN`, `PIXABAY_API_KEY`, `APP_PASSWORD`).

## Images

One 1200×800 featured image per article, with the title in a dark strip across the top:

1. OpenAI suggests photo searches that fit the title ("blood pressure monitor", "doctor measuring blood pressure",
   "salt shaker", ...).
2. **Pixabay** (needs the free `PIXABAY_API_KEY` from https://pixabay.com/api/docs/; free for commercial use, no credit
   required; images must be re-hosted, which the Sanity upload does): a random pick among the best unused matches.
   Then **Pexels** if `PEXELS_API_KEY` is set.
3. If neither has a photo: Openverse CC0 photos. If still nothing: a navy-to-crimson title card.

**A photo is never used twice:** every uploaded image keeps its photo page URL in the Sanity asset description,
and the publisher skips any photo whose URL is already there.
