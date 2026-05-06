import re
import json
import time
import random
import cloudscraper
from tqdm import tqdm


LEAGUE = "Serie_A"
SEASON = 2024

BASE_URL = "https://understat.com"


scraper = cloudscraper.create_scraper(
    delay=10,
    browser={
        "browser": "chrome",
        "platform": "windows",
        "mobile": False
    }
)


def extract_json_variable(html, variable):

    pattern = rf"var {variable}\s*=\s*JSON.parse\('(.+?)'\)"

    match = re.search(pattern, html, re.DOTALL)

    if not match:
        return None

    data = match.group(1)

    decoded = bytes(data, "utf-8").decode("unicode_escape")

    return json.loads(decoded)


def safe_request(url):

    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)"
        ])
    }

    response = scraper.get(url, headers=headers)

    return response.text


def get_league_data():

    url = f"{BASE_URL}/league/{LEAGUE}/{SEASON}"

    print("Fetching league page...")

    html = safe_request(url)

    matches = extract_json_variable(html, "datesData")
    players = extract_json_variable(html, "playersData")

    if matches is None:
        raise Exception("Failed to extract matches (Cloudflare likely triggered)")

    return matches, players


def get_match_shots(match_id):

    url = f"{BASE_URL}/match/{match_id}"

    html = safe_request(url)

    shots = extract_json_variable(html, "shotsData")

    if shots is None:
        raise Exception("shotsData not found")

    return shots


def main():

    print(f"\nDownloading {LEAGUE} {SEASON}\n")

    matches, players = get_league_data()

    print("Matches found:", len(matches))

    all_matches = []
    all_shots = []

    print("\nDownloading shots for each match...\n")

    for match in tqdm(matches):

        match_id = match["id"]

        try:

            shots = get_match_shots(match_id)

            all_matches.append(match)

            for shot in shots:

                shot["match_id"] = match_id
                all_shots.append(shot)

        except Exception as e:

            print("Failed match:", match_id)

        time.sleep(random.uniform(2, 4))

    data = {
        "league": LEAGUE,
        "season": SEASON,
        "players": players,
        "matches": all_matches,
        "shots": all_shots
    }

    with open("serie_a_understat.json", "w", encoding="utf-8") as f:

        json.dump(data, f, indent=2)

    print("\nDownload complete")
    print("Saved to serie_a_understat.json")


if __name__ == "__main__":
    main()