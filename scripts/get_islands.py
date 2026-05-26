import requests
import json
import time
from pathlib import Path

# ============================================
# CONFIG
# ============================================

BASE_URL = "https://api.fortnite.com/ecosystem/v1/islands"

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "islands.json"

PAGE_SIZE = 100

# Optional:
# Stop after X pages for testing
MAX_PAGES = 1000  # Example: 10

# Delay between requests
REQUEST_DELAY = 0.25


# ============================================
# HELPERS
# ============================================

def fetch_page(after_cursor=None):
    """
    Fetch a single page of islands.
    """

    params = {
        "size": PAGE_SIZE
    }

    if after_cursor:
        params["after"] = after_cursor

    response = requests.get(BASE_URL, params=params)

    response.raise_for_status()

    return response.json()


def extract_island_data(raw_island):
    """
    Extract only useful fields.
    """

    return {
        "code": raw_island.get("code"),
        "creatorCode": raw_island.get("creatorCode"),
        "displayName": raw_island.get("displayName"),
        "title": raw_island.get("title"),
        "category": raw_island.get("category"),
        "createdIn": raw_island.get("createdIn"),
        "tags": raw_island.get("tags", [])
    }

def filter_island(island):
    return island.get("creatorCode") != "epic"


# ============================================
# MAIN SCRAPER
# ============================================

def scrape_all_islands():

    all_islands = []

    after_cursor = None
    page_count = 0

    while True:

        try:
            data = fetch_page(after_cursor)

        except requests.HTTPError as e:
            print(f"\nHTTP Error: {e}")
            break

        except Exception as e:
            print(f"\nUnexpected Error: {e}")
            break

        if page_count >= 100:
            islands = data.get("data", [])

            if not islands:
                print("\nNo more islands found.")
                break

            islands = list(filter(filter_island, islands))

            cleaned_islands = [
                extract_island_data(island)
                for island in islands
            ]

            all_islands.extend(cleaned_islands)

            print(
                f"Page {page_count} | "
                f"Fetched {len(islands)} islands | "
                f"Total: {len(all_islands)}"
            )

        page_count += 1

        # Get next cursor
        next_cursor = (
            data.get("meta", {})
            .get("page", {})
            .get("nextCursor")
        )

        # Stop if no more pages
        if not next_cursor:
            print("\nReached final page.")
            break

        after_cursor = next_cursor

        # Testing limiter
        if MAX_PAGES and page_count >= MAX_PAGES:
            print("\nReached MAX_PAGES limit.")
            break

        

        time.sleep(REQUEST_DELAY)

    return all_islands


# ============================================
# SAVE RESULTS
# ============================================

def save_results(islands):

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(islands, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(islands)} islands to:")
    print(OUTPUT_FILE.resolve())


# ============================================
# ENTRY
# ============================================

if __name__ == "__main__":

    islands = scrape_all_islands()

    save_results(islands)