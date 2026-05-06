"""
Import La Liga upcoming fixtures into the DB by parsing Understat HTML via ScraperAPI.
"""
import re
import requests
import psycopg2
from bs4 import BeautifulSoup
from datetime import datetime, timezone

DB = dict(host="localhost", port=5432, user="postgres", password="postgres", dbname="xpalermostat_db")
SCRAPERAPI_KEY = "431f2fa400ff089e9941c13c7d275c42"

LEAGUES_TO_ENSURE = [
    (3, "La Liga",        "La_Liga"),
    (4, "Bundesliga",     "Bundesliga"),
    (5, "Ligue 1",        "Ligue_1"),
    (6, "Premier League", "EPL"),
]

# Current season is 2025/26 (season value = 2025)
IMPORT_TARGETS = [
    {"db_id": 3, "name": "La Liga", "slug": "La_Liga", "season": 2025},
]


def fetch_rendered_html(slug: str, season: int) -> str:
    target = f"https://understat.com/league/{slug}/{season}"
    url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={target}&render=true"
    print(f"  Fetching {target} via ScraperAPI...")
    resp = requests.get(url, timeout=90)
    resp.raise_for_status()
    return resp.text


def parse_upcoming_fixtures(html: str) -> list:
    """
    Parse calendar-date-container divs from Understat rendered page.
    Returns list of {date_str, home, away, is_completed}.
    """
    soup = BeautifulSoup(html, "html.parser")
    fixtures = []

    for date_container in soup.find_all("div", class_="calendar-date-container"):
        date_div = date_container.find("div", class_="calendar-date")
        if not date_div:
            continue
        date_str = date_div.get_text(strip=True)  # e.g. "Sunday, May 03, 2026"

        for game in date_container.find_all("div", class_="calendar-game"):
            match_info = game.find("div", class_="match-info")
            if not match_info:
                continue
            is_result = match_info.get("data-isresult", "false").lower() == "true"

            time_div = match_info.find("div", class_="match-time")
            time_str = time_div.get_text(strip=True) if time_div else "00:00"

            home_div = game.find("div", class_="block-home")
            away_div = game.find("div", class_="block-away")
            if not home_div or not away_div:
                continue

            home_a = home_div.find("a")
            away_a = away_div.find("a")
            if not home_a or not away_a:
                continue

            home_name = home_a.get_text(strip=True)
            away_name = away_a.get_text(strip=True)

            # Parse full datetime
            try:
                dt_str = f"{date_str} {time_str}"
                dt = datetime.strptime(dt_str, "%A, %B %d, %Y %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                try:
                    dt = datetime.strptime(date_str, "%A, %B %d, %Y").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue

            # Try to get goals from score div if completed
            h_goals = a_goals = None
            if is_result:
                score_div = match_info.find("div", class_="match-score")
                if score_div:
                    score_text = score_div.get_text(strip=True)
                    m = re.match(r"(\d+)\s*[-:]\s*(\d+)", score_text)
                    if m:
                        h_goals = int(m.group(1))
                        a_goals = int(m.group(2))

            fixtures.append({
                "home": home_name,
                "away": away_name,
                "datetime": dt,
                "is_completed": is_result,
                "home_goals": h_goals,
                "away_goals": a_goals,
            })

    return fixtures


def get_or_create_team(cur, team_name: str, league_id: int) -> int:
    cur.execute("SELECT id FROM team WHERE name = %s", (team_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO team (name, league_id) VALUES (%s, %s) RETURNING id",
        (team_name, league_id)
    )
    return cur.fetchone()[0]


def run():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    # ── 1. Ensure leagues exist ────────────────────────────────────────
    print("=== Step 1: Ensure leagues in DB ===")
    for lid, lname, slug in LEAGUES_TO_ENSURE:
        cur.execute("SELECT id FROM league WHERE id = %s OR name = %s", (lid, lname))
        if cur.fetchone():
            print(f"  '{lname}' OK")
        else:
            cur.execute(
                "INSERT INTO league (id, name, understat_slug) VALUES (%s, %s, %s)",
                (lid, lname, slug)
            )
            print(f"  Inserted '{lname}' id={lid}")
    conn.commit()

    # ── 2. Fetch and parse each target ────────────────────────────────
    for cfg in IMPORT_TARGETS:
        db_id = cfg["db_id"]
        name  = cfg["name"]
        slug  = cfg["slug"]
        season = cfg["season"]

        print(f"\n=== Step 2: Import {name} {season}/{season+1} ===")
        try:
            html = fetch_rendered_html(slug, season)
            print(f"  HTML length: {len(html)}")
        except Exception as e:
            print(f"  ERROR fetching: {e}")
            continue

        fixtures = parse_upcoming_fixtures(html)
        total = len(fixtures)
        upcoming = [f for f in fixtures if not f["is_completed"]]
        print(f"  Parsed: {total} total fixtures, {len(upcoming)} upcoming")

        if not fixtures:
            print("  No fixtures parsed — check HTML structure")
            continue

        now = datetime.now(timezone.utc)
        inserted = skipped = errors = 0

        for f in fixtures:
            try:
                home_id = get_or_create_team(cur, f["home"], db_id)
                away_id = get_or_create_team(cur, f["away"], db_id)

                # Check for duplicate by teams + datetime
                cur.execute("""
                    SELECT id FROM matchcalendar
                    WHERE home_team_id = %s AND away_team_id = %s
                      AND ABS(EXTRACT(EPOCH FROM (match_datetime - %s))) < 86400
                """, (home_id, away_id, f["datetime"]))
                if cur.fetchone():
                    skipped += 1
                    continue

                cur.execute("""
                    INSERT INTO matchcalendar
                      (league_id, home_team_id, away_team_id, match_datetime,
                       is_completed, is_scraped, home_goals, away_goals)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    db_id, home_id, away_id, f["datetime"],
                    f["is_completed"], False,
                    f["home_goals"], f["away_goals"]
                ))
                inserted += 1

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  WARN {f.get('home')} vs {f.get('away')}: {e}")
                conn.rollback()

        conn.commit()
        print(f"  Result: {inserted} inserted, {skipped} skipped (dup), {errors} errors")

    # ── 3. Verify ─────────────────────────────────────────────────────
    print("\n=== Step 3: Verify ===")
    cur.execute("""
        SELECT l.name,
               COUNT(*) as total,
               SUM(CASE WHEN m.match_datetime > NOW() AND m.is_completed = false THEN 1 ELSE 0 END) as upcoming
        FROM matchcalendar m
        JOIN league l ON m.league_id = l.id
        GROUP BY l.name
        ORDER BY l.name
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} total, {row[2]} upcoming")

    cur.close()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    run()
