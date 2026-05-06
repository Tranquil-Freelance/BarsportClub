import requests
import re
import sys

def main():
    # Use a known match ID (Como vs ?) maybe 21474 (random)
    match_id = 21474
    url = f"https://understat.com/match/{match_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch: {e}")
        sys.exit(1)
    
    html = resp.text
    # Find all var assignments
    var_pattern = r'var\s+(\w+)\s*='
    vars_found = re.findall(var_pattern, html)
    print(f"Found {len(vars_found)} variable assignments")
    unique_vars = set(vars_found)
    print("Unique variables:", sorted(unique_vars))
    
    # Look for matchData specifically
    if 'matchData' in unique_vars:
        print("matchData found!")
        # Extract the JSON
        pattern = r"var\s+matchData\s*=\s*JSON\.parse\s*\(\s*'(.*?)'\s*\)\s*;"
        match = re.search(pattern, html, re.DOTALL)
        if match:
            encoded = match.group(1)
            decoded = encoded.encode('utf-8').decode('unicode_escape')
            import json
            data = json.loads(decoded)
            print("matchData sample:", json.dumps(data, indent=2)[:500])
    else:
        print("matchData not found")
    
    # Look for shotsData
    if 'shotsData' in unique_vars:
        print("shotsData found")
    # Look for rostersData
    if 'rostersData' in unique_vars:
        print("rostersData found")
    # Look for datesData
    if 'datesData' in unique_vars:
        print("datesData found")
    
    # Also extract team names from page title
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string if soup.title else ''
    print("Page title:", title)

if __name__ == '__main__':
    main()