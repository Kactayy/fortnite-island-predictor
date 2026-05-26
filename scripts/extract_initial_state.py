import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import datetime, timezone
import re
import json


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# =========================
# FETCH HISTORY PAGE
# =========================

def fetch_history(island_code):
    url = f"https://fortnite.gg/island/{island_code}/history"

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720},
            locale="en-US"
        )

        page = context.new_page()

        page.goto(url, wait_until="domcontentloaded")

        # SMART WAIT
        page.wait_for_selector(".history-wrap", timeout=10000)
        page.wait_for_selector(".changelog", timeout=5000)

        html = page.content()

        browser.close()

        return html


# =========================
# PLAYER METRICS
# =========================

def extract_fortnitegg_id(soup):

    # Most reliable graph element
    graph = soup.select_one(
        "div.chart, div.js-player-count-chart"
    )

    if graph and graph.get("data-id"):
        return graph.get("data-id")

    # fallback
    for el in soup.select("[data-id]"):

        val = el.get("data-id")

        if val and val.isdigit():
            return val

    return None


def fetch_player_graph_data(fortnitegg_id):

    url = (
        "https://fortnite.gg/player-count-graph"
        f"?metric=uniqueplayers"
        f"&range=all"
        f"&id={fortnitegg_id}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://fortnite.gg/",
        "Origin": "https://fortnite.gg",
        "X-Requested-With": "XMLHttpRequest",
    }

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)

            context = browser.new_context(
                user_agent=headers["User-Agent"],
                locale="en-US"
            )

            page = context.new_page()

            response = page.goto(
                url,
                wait_until="networkidle",
                timeout=30000
            )

            if response is None:
                print("[ERROR] No response from player graph endpoint")
                browser.close()
                return None

            status = response.status

            # print(f"[DEBUG] Player graph status: {status}")

            if status != 200:

                print(f"[ERROR] Failed graph request: {status}")

                browser.close()

                return None

            text = page.text_content("body")

            browser.close()

            if not text:
                return None

            data = json.loads(text)

            print(f"[DEBUG] Player graph data: {data}")

            return data

    except Exception as e:

        print(f"[ERROR] Failed fetching player graph: {e}")

        return None


def process_player_metrics(graph_data):
    """
    fortnite.gg response format:

    {
        "data": {
            "start": 1778544000,
            "step": 86400,
            "values": [67, 192, 101, ...]
        }
    }
    """

    if not graph_data:
        return None

    data = graph_data.get("data")

    if not data:
        return None

    values = data.get("values")

    if not values:
        return None

    daily_values = []

    for value in values:

        if value is None:
            continue

        try:
            value = float(value)
        except:
            continue

        daily_values.append(value)

    if not daily_values:
        return None

    # -----------------------------------
    # FIRST 30 DAYS ONLY
    # -----------------------------------

    first_30 = daily_values[:30]

    avg_30 = sum(first_30) / len(first_30)
    max_30 = max(first_30)

    return {
        "daily_unique_players": daily_values,

        "avg_unique_players_30d": avg_30,
        "max_unique_players_30d": max_30,

        "days_tracked": len(daily_values),

        # useful for debugging / future features
        "graph_start": data.get("start"),
        "graph_step": data.get("step"),
    }


def get_current_thumbnail(soup):
    img = soup.select_one("div.island-gallery img")
    return img.get("src") if img else None


# =========================
# PARSE ALL CHANGES
# =========================

def parse_changelogs(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.select("div.changelog")


def get_description(html):
    soup = BeautifulSoup(html, "html.parser")

    desc = soup.select_one("div.island-desc")

    if not desc:
        return None

    text = desc.get_text("\n", strip=True)

    return text


def extract_v1_date(soup):

    v1 = soup.select_one("div.changelog#v1")

    if not v1:
        return None

    time_tag = v1.select_one("time")

    if not time_tag:
        return None

    dt_str = time_tag.get("datetime")

    if not dt_str:
        return None

    try:

        dt = datetime.fromisoformat(dt_str)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # print(f"[DEBUG] V1 Date: {dt}")

        return dt

    except Exception as e:

        print(f"[ERROR] Failed parsing v1 date: {e}")

        return None


def extract_gallery_data(soup):

    gallery = soup.select_one("div.island-gallery")

    if not gallery:
        return {
            "has_video": 0,
            "num_extra_images": 0,
        }

    # VIDEO
    video_btn = gallery.select_one(
        "div.play-video-btn"
    )

    has_video = 1 if video_btn else 0

    # EXTRA SCREENSHOTS
    extra_images = []

    screenshots = gallery.select(
        "div.island-thumbnails img.screenshot"
    )

    for img in screenshots:

        src = (
            img.get("data-src")
            or img.get("src")
        )

        if not src:
            continue

        if "landscape_comp" in src:
            continue

        extra_images.append(src)

    return {
        "has_video": has_video,
        "num_extra_images": len(extra_images),
    }


def extract_tags_from_html(html):

    soup = BeautifulSoup(html, "html.parser")

    tag_elements = soup.select("div.search-tags-scrollable a.search-tag")

    tags = []

    for tag in tag_elements:

        text = tag.get_text(" ", strip=True)

        tag_name = text.split("\n")[0]
        tag_name = tag_name.split("  ")[0].strip()

        tag_name = re.sub(r"\d[\d,]*$", "", tag_name).strip()

        if tag_name:
            tags.append(tag_name.lower())

    return tags


# =========================
# EXTRACT CHANGE DATA
# =========================

def extract_changes(changelog):

    data = {
        "title": None,
        "description": None,
        "image": None
    }

    # IMAGE changes
    ins_tags = changelog.select("ins.js-modal-changelog")

    for ins in ins_tags:

        href = ins.get("href", "")

        if "landscape_comp" in href:
            data["image"] = href

    # DESCRIPTION changes
    desc = changelog.select_one(".changelog-desc")

    if desc:

        ins = desc.find("ins")

        if ins:
            data["description"] = ins.get_text(" ", strip=True)

    return data


# =========================
# RECONSTRUCT T0
# =========================

def build_initial_state(island_code, islands_map):

    html = fetch_history(island_code)

    soup = BeautifulSoup(html, "html.parser")

    changelogs = parse_changelogs(html)

    description = get_description(html)

    start_date = extract_v1_date(soup)

    gallery_data = extract_gallery_data(soup)

    # -----------------------------------
    # NEW: FETCH PLAYER METRICS
    # -----------------------------------

    fortnitegg_id = extract_fortnitegg_id(soup)

    player_metrics = None

    if fortnitegg_id:

        # print(f"[DEBUG] FortniteGG ID: {fortnitegg_id}")

        graph_data = fetch_player_graph_data(
            fortnitegg_id
        )

        player_metrics = process_player_metrics(
            graph_data
        )

        print(f"[DEBUG] Player metrics: {player_metrics}")

    initial = {
        "title": None,
        "description": description,
        "image": gallery_data.get("image"),
        "start_date": start_date.isoformat() if start_date else None,
        "has_video": gallery_data.get("has_video"),
        "num_extra_images": gallery_data.get("num_extra_images"),

        # NEW
        "player_metrics": player_metrics,
    }

    # print(f"[DEBUG] Initial State: {initial}")

    # HISTORY
    for cl in reversed(changelogs):

        changes = extract_changes(cl)

        for k in [
            "title",
            "description",
            "image",
            "has_video",
            "num_extra_images"
        ]:

            if changes.get(k) and initial[k] is None:
                initial[k] = changes[k]

    # CURRENT PAGE FALLBACK
    if not initial["image"]:
        initial["image"] = get_current_thumbnail(soup)

    # islands.json FALLBACK
    meta = islands_map.get(island_code, {})

    if not initial["title"]:
        initial["title"] = meta.get("title")

    if not initial["description"]:
        initial["description"] = meta.get("description")

    # print(f"[DEBUG] Final Initial State: {initial}")

    return initial