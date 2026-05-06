#!/usr/bin/env python3
import requests
import re
import sys
import time

def fetch_match(match_id):
    url = f"https://understat.com/match/{match_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 404:
            return None
        else:
            raise

def parse_match(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string if soup.title else ''
    # Extract league pattern "| La liga |" or "| Serie A |"
    league = None
    if 'Serie A' in title:
        league = 'Serie A'
    elif 'La liga' in title:
        league = 'La liga'
    elif 'Premier League' in title:
        league = 'Premier League'
    # Extract teams
    pattern = r'(.+?)\s+[-–]\s+(.+?)\s+\|'  # "Team1 - Team2 |"
    match = re.search(pattern, title)
    home = away = None
    if match:
        home, away = match.group(1), match.group(2)
    else:
        # try "vs"
        pattern2 = r'(.+?)\s+vs\s+(.+?)\s+\|'
        match2 = re.search(pattern2, title)
        if match2:
            home, away = match2.group(1), match2.group(2)
    return title, league, home, away

def main():
    # Serie A 2024/25 match IDs likely in range 21000-25000? Let's sample.
    start = 21000
    end = 21050  # just 50 matches
    found = []
    for mid in range(start, end+1):
        print(f"Checking match {mid}...", end='')
        html = fetch_match(mid)
        if html is None:
            print(" 404")
            continue
        title, league, home, away = parse_match(html)
        print(f" {league} {home} - {away}")
        if league == 'Serie A' and ('Como' in str(home) or 'Como' in str(away)):
            print(f"  *** FOUND COMO MATCH ID: {mid} ***")
            found.append((mid, home, away))
        time.sleep(1)  # be polite
    print(f"\nFound {len(found)} Como matches:")
    for mid, home, away in found:
        print(f"  {mid}: {home} vs {away}")

if __name__ == '__main__':
    main()