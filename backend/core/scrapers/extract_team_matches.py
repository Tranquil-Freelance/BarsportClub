#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.scraper.understat_parser import fetch_html, extract_json_from_script

def get_team_matches(team_slug, season_year):
    url = f'https://understat.com/team/{team_slug}/{season_year}'
    html = fetch_html(url)
    # Try common variable names
    for var_name in ['matchesData', 'datesData', 'teamData', 'data']:
        try:
            data = extract_json_from_script(html, var_name)
            print(f"Found variable {var_name}")
            return data
        except ValueError:
            continue
    raise ValueError('No known data variable found')

def main():
    try:
        data = get_team_matches('Como', 2025)
        print(f"Data type: {type(data)}")
        if isinstance(data, list):
            print(f"Number of items: {len(data)}")
            for i, item in enumerate(data[:10]):
                print(f"{i}: {item}")
        elif isinstance(data, dict):
            print("Keys:", data.keys())
            # maybe match IDs are nested
            import json
            print(json.dumps(data, indent=2)[:500])
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()