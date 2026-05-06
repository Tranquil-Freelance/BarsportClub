import requests
import re

html = requests.get('https://understat.com/match/27362', headers={'User-Agent': 'Mozilla/5.0'}).text
print('HTML length:', len(html))

# find all var assignments with JSON.parse
pattern = re.compile(r'var\s+(\w+)\s*=\s*JSON\.parse', re.IGNORECASE)
matches = pattern.findall(html)
print('All JSON.parse variables:', matches)

# search for shots
shots_pattern = re.compile(r'shots', re.IGNORECASE)
shots_matches = shots_pattern.findall(html)
print('Occurrences of shots:', len(shots_matches))
if shots_matches:
    # find context
    for m in re.finditer(r'var.*?shots.*?=.*?JSON\.parse', html, re.DOTALL | re.IGNORECASE):
        print('Found:', m.group()[:200])

# also look for match_info
if 'match_info' in html:
    idx = html.find('match_info')
    print('match_info found at', idx)
    print('Context:', html[idx:idx+500])

# write a snippet to file for inspection
with open('debug_output.txt', 'w', encoding='utf-8') as f:
    f.write(html[:10000])