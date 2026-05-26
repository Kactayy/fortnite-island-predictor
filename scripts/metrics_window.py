import requests
import re
from datetime import datetime, timedelta, timezone


BASE = "https://api.fortnite.com/ecosystem/v1"


# ============================================
# HELPERS
# ============================================

def format_fortnite_time(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def parse_api_min_date(error_text):
    """
    Extract:
    'Thu, 14 May 2026 00:00:00 GMT'

    from:
    'The from timestamp cannot be before Thu, 14 May 2026 00:00:00 GMT.'
    """

    #https://fortnite.gg/player-count-graph?range=1d&id=529631

    match = re.search(
        r"before (.+ GMT)",
        error_text
    )

    if not match:
        return None

    try:
        return datetime.strptime(
            match.group(1),
            "%a, %d %b %Y %H:%M:%S GMT"
        ).replace(tzinfo=timezone.utc)

    except Exception:
        return None


def build_metrics_url(island_code, start_date):

    now = datetime.now(timezone.utc)

    yesterday_start = (now - timedelta(days=1)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    use_default_endpoint = start_date >= yesterday_start

    if use_default_endpoint:

        return f"{BASE}/islands/{island_code}/metrics"

    end_date = start_date + timedelta(days=30)

    if end_date > now:
        end_date = now

    start = format_fortnite_time(start_date)
    end = format_fortnite_time(end_date)

    return (
        f"{BASE}/islands/{island_code}/metrics"
        f"?from={start}"
        f"&to={end}"
    )


def fetch_metrics(island_code, start_date):

    def make_request(date_to_use):

        url = build_metrics_url(
            island_code,
            date_to_use
        )

        r = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        return r

    try:

        r = make_request(start_date)

        # -----------------------------------
        # Retry if API rejects old timestamp
        # -----------------------------------

        if r.status_code == 400:

            try:
                error_data = r.json()

                message = (
                    error_data.get("errorMessage")
                    or error_data.get("message")
                    or str(error_data)
                )

                print(f"[DEBUG] 400 ERROR: {message}")

                min_date = parse_api_min_date(message)

                if min_date:

                    print(
                        f"[DEBUG] Retrying with API minimum date: "
                        f"{min_date}"
                    )

                    r = make_request(min_date)

            except Exception as parse_error:

                print(
                    f"[DEBUG] Failed parsing 400 response: "
                    f"{parse_error}"
                )

        print(f"[DEBUG] Status Code: {r.status_code}")

        r.raise_for_status()

        return r.json()

    except Exception as e:

        print(f"[DEBUG] fetch_metrics FAILED: {e}")

        return None

# ============================================
# EXTRACTION
# ============================================

def extract_latest(arr, key="value", metric_name="unknown"):

    if not arr:

        return None

    # newest → oldest
    for i, x in enumerate(reversed(arr)):

        val = x.get(key)

        if val is not None:
            return val

    # print(f"[DEBUG] {metric_name}: ALL VALUES NONE")

    return None


# ============================================
# PROCESS
# ============================================

def process_metrics(raw):

    if raw is None:
        return None

    processed = {

        "uniquePlayers": extract_latest(
            raw.get("uniquePlayers"),
            metric_name="uniquePlayers"
        ),

        "plays": extract_latest(
            raw.get("plays"),
            metric_name="plays"
        ),

        "favorites": extract_latest(
            raw.get("favorites"),
            metric_name="favorites"
        ),

        "recommendations": extract_latest(
            raw.get("recommendations"),
            metric_name="recommendations"
        ),

        "peakCCU": extract_latest(
            raw.get("peakCCU"),
            metric_name="peakCCU"
        ),

        "minutesPlayed": extract_latest(
            raw.get("minutesPlayed"),
            metric_name="minutesPlayed"
        )
    }

    # print(f"[DEBUG] Final Processed Metrics:")
    # print(processed)

    return processed

# import requests
# from datetime import datetime, timedelta, timezone


# BASE = "https://api.fortnite.com/ecosystem/v1"


# def format_fortnite_time(dt):
#     return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

# def build_metrics_url(island_code, start_date):

#     now = datetime.now(timezone.utc)

#     yesterday_start = (now - timedelta(days=1)).replace(
#         hour=0, minute=0, second=0, microsecond=0
#     )

#     if start_date >= yesterday_start:
#         return (
#             f"{BASE}/islands/{island_code}/metrics"
#         )

#     end_date = start_date + timedelta(days=30)

#     if end_date > now:
#         end_date = now

#     start = format_fortnite_time(start_date)
#     end = format_fortnite_time(end_date)

#     url = (
#         f"{BASE}/islands/{island_code}/metrics"
#         f"?from={start}"
#         f"&to={end}"
#     )

#     return url


# def fetch_metrics(island_code, start_date):

#     url = build_metrics_url(island_code, start_date)

#     r = requests.get(url, timeout=30)
#     r.raise_for_status()

#     # print(f"the metrics url is {url}")
#     # print(f"the metrics are {r.json()}")

#     return r.json()


# def extract_latest(arr, key="value"):

#     if not arr:
#         return None

#     for x in reversed(arr):
#         if x.get(key) is not None:
#             return x.get(key)

#     return None


# def process_metrics(raw):

#     return {
#         "uniquePlayers": extract_latest(raw.get("uniquePlayers")),
#         "plays": extract_latest(raw.get("plays")),
#         "favorites": extract_latest(raw.get("favorites")),
#         "recommendations": extract_latest(raw.get("recommendations")),
#         "peakCCU": extract_latest(raw.get("peakCCU")),
#         "minutesPlayed": extract_latest(raw.get("minutesPlayed"))
#     }