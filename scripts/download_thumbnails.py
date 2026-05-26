import json
import re
import time
import random
from pathlib import Path

from playwright.sync_api import sync_playwright


# ============================================
# CONFIG
# ============================================

ISLANDS_FILE = Path("data/islands.json")

THUMBNAIL_DIR = Path("data/thumbnails")
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

FAILED_FILE = Path("data/failed_thumbnails.json")

REQUEST_DELAY = 0.3


# Fortnite CDN regex
THUMBNAIL_REGEX = re.compile(
    r'https://cdn[^"]+landscape_comp\.jpeg'
)


# ============================================
# HELPERS
# ============================================

def load_islands():
    with open(ISLANDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_fortnite_url(creator_code, island_code):
    return f"https://www.fortnite.com/@{creator_code}/{island_code}"


def extract_thumbnail_url(html):
    match = THUMBNAIL_REGEX.search(html)
    return match.group(0) if match else None

def extract_thumbnail(page, url):
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    imgs = page.query_selector_all("img")

    for img in imgs:

        src = img.get_attribute("src")

        if not src:
            continue

        if "landscape_comp.jpeg" not in src:
            continue

        # Ignore tiny related thumbnails/icons
        box = img.bounding_box()

        if not box:
            continue

        width = box["width"]
        height = box["height"]

        classImg = img.get_attribute("class")

        if "no8po010 no8po013" not in classImg:
            continue

        # Main thumbnail is large
        if width >= 400 and height >= 200:
            return src

    return None


# ============================================
# PLAYWRIGHT PAGE FETCH
# ============================================

def fetch_page_html(page, url):
    """
    Loads a Fortnite island page using real browser context.
    """

    page.goto(url, wait_until="domcontentloaded", timeout=20000)

    # Sometimes content loads slightly after network idle
    page.wait_for_timeout(1500)

    return page.content()


# ============================================
# DOWNLOAD IMAGE
# ============================================

def download_image(url, save_path, page):

    try:
        response = page.request.get(url)

        if response.status != 200:
            return False

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(response.body())

        return True

    except Exception as e:
        print(f"Image download failed: {e}")
        return False


# ============================================
# MAIN SCRAPER
# ============================================

def scrape_thumbnails():

    islands = load_islands()
    failed = []

    total = len(islands)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True  # set False for debugging
        )

        for i, island in enumerate(islands, start=1):
            if i < 11:
                continue
            if i > 12:
                break
            island_code = island["code"]
            creator_code = island["creatorCode"]

            url = build_fortnite_url(creator_code, island_code)

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                locale="en-US"
            )

            page = context.new_page()

            try:
                thumbnail_url = extract_thumbnail(page, url)

                if not thumbnail_url:
                    print(f"[{i}] NO THUMBNAIL: {island_code}")
                    continue

                download_image(thumbnail_url, THUMBNAIL_DIR / f"{island_code}.jpg", page)

                print(f"[{i}] OK: {island_code}")

            except Exception as e:
                print(f"[{i}] FAILED: {island_code} | {e}")

            finally:
                context.close()   # 👈 CRITICAL

            time.sleep(random.uniform(0.15, 0.4))

        browser.close()

    return failed


# ============================================
# SAVE FAILURES
# ============================================

def save_failures(failed):

    with open(FAILED_FILE, "w", encoding="utf-8") as f:
        json.dump(failed, f, indent=2)

    print(f"\nSaved failures: {len(failed)} → {FAILED_FILE}")


# ============================================
# ENTRY
# ============================================

if __name__ == "__main__":

    failed = scrape_thumbnails()
    save_failures(failed)

    print("\nDone.")