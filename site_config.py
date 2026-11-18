"""
Site-specific settings for severehypertension.net.

Everything that ties this publisher to one website lives in this file.
The site runs on Next.js + Sanity (Vercel), so articles are published straight to Sanity.
"""

SITE_NAME = "Severe Hypertension"
SITE_DOMAIN = "severehypertension.net"
SITE_URL = "https://severehypertension.net"  # primary domain (bare, no www)
PAGE_ICON = "🩺"

# OpenAI model used for articles and FAQs (override with the OPENAI_MODEL secret)
DEFAULT_OPENAI_MODEL = "gpt-4o"

# ------------------------------------------------------------------------------
# Categories: the site's Sanity category titles (they must match exactly).
# Value = Sanity document id, for reference. URLs are unchanged from WordPress
# (e.g. "Severe Hypertension News" is still /category/severe-hypertension-news/).
# The textbook chapter categories (Models of Stress, Theories of Stress, ...) are left out on purpose.
# ------------------------------------------------------------------------------
CATEGORY_MAP = {
    "High Blood Pressure Guide": "category-high-blood-pressure-guide",
    "Severe Hypertension News": "category-severe-hypertension-news",
    "High Blood Pressure": "category-high-blood-pressure",
    "Causes of High Blood Pressure": "category-causes-of-high-blood-pressure",
    "Symptoms of High Blood Pressure": "category-symptoms-high-blood-pressure",
    "High Blood Pressure Warning Signs": "category-high-blood-pressure-warning-signs",
    "High Blood Pressure Diagnosis": "category-high-blood-pressure-diagnosis",
    "High Blood Pressure: Living & Managing": "category-high-blood-pressure-managing",
    "Hypertension Treatment & Care": "category-hypertension-treatment-care",
    "Diet For High Blood Pressure": "category-diet-for-high-blood-pressure",
    "Hypertension Support Blog": "category-hypertension-support-blog",
    "Measurement of Blood Pressure": "category-measurement-of-blood-pressure",
    "Blood Pressure Monitoring during Daily Life": "category-blood-pressure-monitoring-during-daily-life",
    "Primary (essential) hypertension": "category-primary-hypertension",
    "Secondary Hypertension": "category-secondary-hypertension",
    "Stress and Essential Hypertension": "category-stress-and-essential-hypertension",
    "Coronavirus and Hypertension": "category-coronavirus-and-hypertension",
}
DEFAULT_CATEGORIES = ["High Blood Pressure Guide"]
# Every new article is also put in these categories (after the chosen ones). None for this site:
# news articles go to "Severe Hypertension News" through NEWS_CATEGORY_NAMES, as on WordPress.
ALWAYS_CATEGORIES = []

# ------------------------------------------------------------------------------
# Writing rules
# ------------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You write health education blog posts for Severe Hypertension (severehypertension.net), "
    "an independent information site about high blood pressure for adults in the United States: "
    "blood pressure readings and categories, home monitoring, causes and risk factors, symptoms and warning signs, "
    "hypertensive crisis, lifestyle changes (salt, the DASH diet, exercise, weight, alcohol, sleep, stress), "
    "blood pressure medicines in general terms, and the heart, kidney, brain and eye problems high blood pressure can cause. "
    "Tone: Calm, warm, plain-English, active voice, short simple sentences. Write like an experienced "
    "health writer explaining things to a friend, not like a textbook. "
    "Do NOT use em dashes, AI-style labels, or generic intros such as 'In today's world'. "
    "Length: ~1,200 words. Structure: Question-based H2 headings. "
    "Medical accuracy rules: Only state well-established facts that match current mainstream guidance "
    "(for example the American Heart Association, the American College of Cardiology, the CDC, the NHLBI "
    "and major academic medical centers). Use the AHA/ACC blood pressure categories (normal below 120/80, "
    "elevated 120-129 and below 80, stage 1 130-139 or 80-89, stage 2 140/90 or higher, "
    "hypertensive crisis above 180 and/or above 120). "
    "Never invent statistics, studies, quotes, doctors, or patient stories. "
    "If you mention a number, use widely accepted figures only and keep them general. "
    "Never give personal dosing instructions and never tell readers to start, stop or change a medicine on their own; "
    "say to follow the label or ask a doctor or pharmacist. "
    "Never claim a food, supplement, or treatment cures high blood pressure. "
    "Severe Hypertension is not a clinic. Do not invite readers to book appointments with Severe Hypertension; "
    "encourage them to talk with their own doctor, a cardiologist, or a pharmacist. "
    "CRITICAL LENGTH RULE: You MUST write 3 to 4 detailed paragraphs under EVERY SINGLE H2 to ensure "
    "the article reaches 1,200+ words. No brief summaries."
)

ARTICLE_PROMPT_TEMPLATE = """
Write an in-depth, trustworthy health education blog post for Severe Hypertension about: "{topic}".

Strict Article Requirements:
1. Every major section must start with a question-based H2 heading ending in a question mark (e.g., '## What Counts as a Hypertensive Crisis?').
2. Include at least 5 to 7 question-based H2 sections.
3. Under EVERY SINGLE H2 heading, write 3 to 4 well-developed paragraphs covering readings, symptoms, causes, risk factors, tests, home monitoring, lifestyle changes, treatment options, or prevention as they relate to the topic.
4. One H2 section must explain when to see a doctor, including warning signs that need urgent care: a reading above 180/120 with chest pain, shortness of breath, back pain, numbness or weakness, trouble seeing or speaking, confusion, or a severe headache means calling 911 right away. A reading above 180/120 without symptoms means waiting a few minutes, measuring again, and calling the doctor if it is still that high.
5. Keep individual sentences short, natural, and clear. Avoid filler phrases, em dashes (—), and artificial AI introductions.
6. Do not include an FAQ section in this body content (the FAQ is generated separately).
7. Do not add a disclaimer (one is added automatically).
8. Total word count must be 1,200+ words.
"""

FAQ_SYSTEM_PROMPT = (
    "You are a careful health educator who writes topic-specific FAQ sections about high blood pressure. "
    "You always reply with valid JSON."
)

FAQ_PROMPT_TEMPLATE = """
Generate 12 frequently asked questions and answers for a blog post titled: "{topic}".

Strict Specifications:
1. Every question MUST be directly about the topic of the title above. These are the questions a reader of that specific article would ask. Do not drift to unrelated conditions or treatments that the title does not mention.
2. Write as Severe Hypertension, an independent high blood pressure information site. Severe Hypertension is not a clinic and does not treat patients.
3. Requirements for every answer: EXACTLY 3 sentences. Helpful, reassuring, plain-English tone. Short, natural sentences in active voice. No em dashes.
4. Never invent statistics, studies, prices, brand claims, or guarantees. Never give personal dosing instructions or tell readers to stop a medicine.
5. The last question must be about when to see a doctor for this topic, and it must mention calling 911 for a reading above 180/120 with symptoms such as chest pain, shortness of breath, numbness or weakness, vision changes, or trouble speaking.

Output Format:
Return ONLY a JSON object of this shape:
{{"faqs": [{{"question": "...", "answer": "..."}}, ...]}}
with exactly 12 items.
"""

# Sample topics for the quick-select buttons
SAMPLE_TOPICS = [
    "Hypertensive Crisis: Which Blood Pressure Readings Need Emergency Care",
    "How to Measure Your Blood Pressure Correctly at Home",
    "The DASH Diet: A Simple Eating Plan to Lower Blood Pressure",
    "Resistant Hypertension: Why Blood Pressure Stays High Despite Medicine",
]

# ------------------------------------------------------------------------------
# Formatting
# ------------------------------------------------------------------------------
H2_OPEN_TAG = "<h2>"
# New article URLs have at most this many words. OpenAI picks the main keyword (SLUG_PROMPT);
# if that fails, the first words of the title are used with filler words ("what", "and", "the") dropped.
# A "-2" is still added when the URL is already taken.
SLUG_MAX_WORDS = 4
SLUG_PROMPT = """
Write a short SEO URL slug for a high blood pressure article titled: "{topic}".

Rules:
- At most {max_words} words in total, lowercase, joined by hyphens. Every number counts as a word.
- Use the article's main search keyword, the words people would type into Google. Keep the most important
  words and drop filler words (what, how, your, and, the, of, to).
- Plain English words only. No dates, no site name, no stop words at the start or end.

Examples: "Hypertensive Crisis: Which Blood Pressure Readings Need Emergency Care" -> "hypertensive-crisis-readings";
"How to Measure Your Blood Pressure Correctly at Home" -> "measure-blood-pressure-home".

Return ONLY JSON: {{"slug": "..."}}
"""
FAQ_HEADING = "Frequently Asked Questions"

# severehypertension.net has no content-block shortcodes; add them here if you create some
SHORTCODES_LIST = []

KEYWORDS_TO_BOLD = [
    "high blood pressure",
    "hypertensive crisis",
    "blood pressure reading",
    "systolic",
    "diastolic",
    "home blood pressure monitor",
    "DASH diet",
    "sodium",
    "potassium",
    "stroke",
    "heart attack",
    "kidney disease",
    "cardiologist",
    "prevention",
    "lifestyle changes",
    "medication",
]

# Internal links (all checked: return HTTP 200 on the Next.js site, 2026-11-18)
INTERNAL_LINKS = [
    {
        "keywords": ["lower your blood pressure", "lower blood pressure", "lowering blood pressure", "reduce blood pressure"],
        "html": '<a href="https://severehypertension.net/how-to-lower-your-blood-pressure/">lower your blood pressure</a>',
    },
    {
        "keywords": ["DASH diet", "DASH eating plan"],
        "html": '<a href="https://severehypertension.net/what-is-dash-diet/">DASH diet</a>',
    },
    {
        "keywords": ["potassium"],
        "html": '<a href="https://severehypertension.net/potassium-helps-lower-blood-pressure/">potassium</a>',
    },
    {
        "keywords": ["less salt", "cut salt", "salt intake", "sodium intake", "too much salt"],
        "html": '<a href="https://severehypertension.net/replace-salt-with-these-herb-blends/">cutting back on salt</a>',
    },
    {
        "keywords": ["medicines that raise blood pressure", "decongestants", "NSAIDs", "pain relievers"],
        "html": '<a href="https://severehypertension.net/medicines-that-can-make-blood-pressure-rise/">medicines that can raise blood pressure</a>',
    },
    {
        "keywords": ["hypertensive crisis", "blood pressure skyrockets", "dangerously high", "180/120"],
        "html": '<a href="https://severehypertension.net/what-should-you-do-if-your-blood-pressure-skyrockets/">a hypertensive crisis</a>',
    },
    {
        "keywords": ["white coat hypertension", "white coat effect", "white-coat"],
        "html": '<a href="https://severehypertension.net/isolated-clinic-hypertension-white-coat-hypertension/">white coat hypertension</a>',
    },
    {
        "keywords": ["ambulatory blood pressure monitoring", "ambulatory monitoring", "24-hour monitor"],
        "html": '<a href="https://severehypertension.net/ambulatory-blood-pressure-monitoring/">ambulatory blood pressure monitoring</a>',
    },
    {
        "keywords": ["home blood pressure monitor", "home monitor", "upper arm cuff", "arm cuff", "home monitoring"],
        "html": '<a href="https://severehypertension.net/automatic-arm-monitor-best-for-checking-blood-pressure/">an automatic upper-arm monitor</a>',
    },
    {
        "keywords": ["complications", "heart failure", "organ damage", "consequences"],
        "html": '<a href="https://severehypertension.net/consequences-of-hypertension/">complications of high blood pressure</a>',
    },
    {
        "keywords": ["causes of high blood pressure", "risk factors", "what causes high blood pressure"],
        "html": '<a href="https://severehypertension.net/what-causes-high-blood-pressure-how-to-minimize-your-risk/">what causes high blood pressure</a>',
    },
    {
        "keywords": ["stress"],
        "html": '<a href="https://severehypertension.net/stress-and-essential-hypertension/">stress and blood pressure</a>',
    },
    {
        "keywords": ["symptoms of high blood pressure", "no symptoms", "silent killer"],
        "html": '<a href="https://severehypertension.net/symptoms-of-essential-hypertension/">symptoms of high blood pressure</a>',
    },
    {
        "keywords": ["at night", "nighttime blood pressure", "nocturnal", "during sleep"],
        "html": '<a href="https://severehypertension.net/nocturnal-dipping-of-blood-pressure/">nighttime blood pressure</a>',
    },
    {
        "keywords": ["dementia", "memory", "cognitive decline"],
        "html": '<a href="https://severehypertension.net/studies-link-blood-pressure-dementia/">blood pressure and dementia</a>',
    },
]

FALLBACK_LINK_SENTENCE = (
    '<p>Want to learn more? Read our guide on '
    '<a href="https://severehypertension.net/how-to-lower-your-blood-pressure/">how to lower your blood pressure</a> and our overview of '
    '<a href="https://severehypertension.net/what-causes-high-blood-pressure-how-to-minimize-your-risk/">what causes high blood pressure</a>.</p>'
)

# Added at the end of every post (after the FAQ)
MEDICAL_DISCLAIMER_HTML = (
    '<p><em>This article is for general information only and is not medical advice. '
    'Always talk with your doctor about your blood pressure and treatment, and do not start or stop a medicine on your own. '
    'If your blood pressure is above 180/120 and you have chest pain, shortness of breath, numbness or weakness, '
    'vision changes, or trouble speaking, call 911 right away.</em></p>'
)

# ------------------------------------------------------------------------------
# Meta description
# ------------------------------------------------------------------------------
META_DESC_SUFFIX = "Learn more at Severe Hypertension."
META_DESC_FALLBACK = "Clear, trustworthy information on high blood pressure: readings, causes, warning signs, treatment, and prevention."
META_DESC_MAX_CHARS = 160

# ------------------------------------------------------------------------------
# Images
# ------------------------------------------------------------------------------
IMAGE_COUNT = 1  # one featured image per post
IMAGE_SIZE = (1200, 800)  # featured image size (photo is cropped to fill it)
TITLE_CARD_COLORS = ((10, 21, 40), (209, 42, 67))  # Pulse navy -> crimson

# Open-license topic photos (Openverse = WordPress.org's search of Creative Commons media).
# CC0 only: free for commercial use, no attribution required. StockSnap has modern stock photos.
USE_OPEN_PHOTOS = True
OPENVERSE_API = "https://api.openverse.org/v1/images/"
OPENVERSE_SOURCES = ["stocksnap"]          # tried first
OPENVERSE_FALLBACK_SOURCES = ["stocksnap", "flickr", "wikimedia"]  # broader second pass
OPENVERSE_LICENSE = "cc0,pdm"
PHOTO_OVERLAY_ALPHA = 30    # 0-255 light navy tint over the whole photo (0 = none)
TITLE_BAR_RATIO = 0.20      # title strip covers the top 20% of the image
TITLE_BAR_ALPHA = 150       # 0-255 darkness of the title strip
TITLE_MAX_FONT = 44         # max title font size in px (on a 1200px-wide image)
SHOW_DOMAIN_ON_IMAGE = False
GRAYSCALE_IMAGES = False    # True = every featured image is saved in black and white

PHOTO_QUERY_PROMPT = """
Suggest stock photo search phrases (for Pixabay / Pexels) for the featured image of a high blood pressure article titled: "{topic}".

Rules:
- 6 phrases, best first. Each is 2 to 4 plain visual words a stock photo site would tag.
- The photo must clearly fit BLOOD PRESSURE or HEART HEALTH to a reader. Good examples:
  "blood pressure monitor", "doctor measuring blood pressure", "blood pressure cuff arm", "stethoscope heart",
  "senior man doctor", "woman checking blood pressure", "salt shaker", "healthy food vegetables",
  "man jogging park", "fresh fruit bowl", "woman yoga relax", "pharmacist pills".
- Pick phrases that suit THIS title, so different articles get different pictures.
- Nothing graphic or frightening: no surgery, no blood, no people collapsing, no hospital beds with tubes.
- No brand names, no drug names, no text.

Return ONLY JSON: {{"queries": ["...", "..."]}}
"""
# Used if OpenAI can't suggest phrases (shuffled each time, so articles still get different photos)
DEFAULT_PHOTO_QUERIES = [
    "blood pressure monitor", "doctor measuring blood pressure", "stethoscope heart", "senior man doctor",
    "healthy food vegetables", "woman checking blood pressure",
]

# Last-resort Openverse phrases (only when Pixabay/Pexels give nothing), so an article still gets a photo
# instead of a plain title card
OPENVERSE_GENERIC_QUERIES = [
    "doctor patient", "stethoscope", "blood pressure", "senior man", "hospital", "woman doctor",
    "walking", "vegetables", "fruit", "nurse", "running", "heart",
]

# Pexels/Pixabay photo descriptions containing these words are skipped
PEXELS_ALT_BLOCKLIST = [
    "wound", "surgery", "operation", "corpse", "skull", "funeral", "grave", "cigarette", "smoking",
    "halloween", "zombie", "nude", "naked", "blood drop", "syringe", "text", "logo", "sign",
]

# Words that suggest the wrong kind of image for a health site
PHOTO_TITLE_BLOCKLIST = [
    "quote", "typography", "text", "logo", "sign", "advert", "poster", "cure", "dog", "cat",
    "chart", "graph", "map", "diagram", "screenshot", "etching", "engraving", "illustration",
    "tire", "gauge", "pump", "boiler",
]

# ------------------------------------------------------------------------------
# Daily news auto-publisher (autopublish.py, run by GitHub Actions)
# ------------------------------------------------------------------------------
TIMEZONE = "America/Los_Angeles"
PUBLISH_HOURS = [9, 14]          # local times: 9am = 1st headline, 2pm = 2nd headline
LAST_CATCH_UP_HOUR = 17          # a missed slot is made up by the hourly runs until 5:59pm
NEWS_QUERY = 'hypertension OR "high blood pressure" OR "blood pressure"'
NEWS_WINDOW = "1d"               # Google News "when:" filter (last 24 hours)
NEWS_FALLBACK_WINDOW = "3d"      # used if nothing new in the last day
NEWS_SOURCE_BLOCKLIST = ["YouTube", "TikTok", "Facebook", "Instagram", "Reddit"]
NEWS_CATEGORY_NAMES = ["Severe Hypertension News"]
# Fallback filter when OpenAI can't judge the headlines
NEWS_KEYWORD_RE = r"\b(hypertensi\w*|blood pressure|antihypertensive\w*|preeclampsia|stroke|cardiovascular)\b"

NEWS_PICK_PROMPT = """
Below are recent news headlines found by searching Google News for hypertension, high blood pressure,
and blood pressure.

{listing}

Keep ONLY headlines that are genuinely about human blood pressure or closely related heart, kidney and
stroke health: research, treatments, drugs, guidelines, screening, home monitoring, diet and lifestyle,
pregnancy-related high blood pressure, risk factors, prevention, or patient care. REJECT business, stock
or "market size" reports, "pressure" used in a non-medical sense (political, financial, sports, tire or
water pressure), pulmonary or portal hypertension unless clearly explained, celebrity gossip, crime,
product promotions, miracle-cure claims, animal health, and non-English headlines.

For each kept headline write an original, accurate, SEO-friendly article title for Severe Hypertension
(55-75 characters, plain English, no clickbait, no em dashes, do not copy the headline word for word,
do not promise cures).

Return ONLY JSON: {{"picks": [{{"index": <number>, "title": "..."}}]}}
Return an empty list if none qualify.
"""

NEWS_ARTICLE_EXTRA = """
News context: this article is prompted by a recent news report.
- Headline: "{headline}"
- Published by: {source}

How to use it:
- In the first section, briefly say what the news report covers, using ONLY what the headline states.
  You have not read the report, so do NOT invent study details, numbers, names, dates, quotes, or results.
  Use cautious wording such as "a recent report from {source} highlights..." and "early research suggests".
- Then write a helpful, accurate explainer on the wider topic for readers who have or worry about high blood pressure:
  background, what is already well established, what it may mean for patients, and practical next steps.
- Do not include a link or a sources list (one is added automatically).
"""

# ------------------------------------------------------------------------------
# Sanity (the live site: Next.js + Sanity on Vercel)
# ------------------------------------------------------------------------------
SANITY_PROJECT_ID = "epwrfm14"
SANITY_DATASET = "production"
# Every article is credited to the site's only author (Sanity document id): "Severe Hypertension Network",
# the byline the WordPress posts used.
SANITY_AUTHOR_ID = "author-david"
# Marker for auto-published news posts (used by the daily slot count).
SOURCE_MARKER = "sh-news-source"
