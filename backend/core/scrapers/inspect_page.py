import requests
import re
url = 'https://understat.com/league/Serie_A/2025'
headers = {'User-Agent': 'Mozilla/5.0'}
resp = requests.get(url, headers=headers)
html = resp.text
# Find all script tags
import bs4
soup = bs4.BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')
for script in scripts:
    if script.string:
        # Look for var assignments
        lines = script.string.split('\n')
        for line in lines:
            if 'var ' in line and '=' in line:
                print(line.strip()[:200])
        # Also look for datesData
        if 'datesData' in script.string:
            print('Found datesData in script')
            # extract the line
            for line in script.string.split('\n'):
                if 'datesData' in line:
                    print(line.strip()[:200])
                    break
        # Look for matchesData
        if 'matchesData' in script.string:
            print('Found matchesData in script')
            for line in script.string.split('\n'):
                if 'matchesData' in line:
                    print(line.strip()[:200])
                    break
        # Look for teamData
        if 'teamData' in script.string:
            print('Found teamData in script')
            for line in script.string.split('\n'):
                if 'teamData' in line:
                    print(line.strip()[:200])
                    break