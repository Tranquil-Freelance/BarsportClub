import requests
import re

js_url = 'https://understat.com/js/main.min.js?t=1765138215'
resp = requests.get(js_url, headers={'User-Agent': 'Mozilla/5.0'})
js = resp.text

# Search for shotsData
if 'shotsData' in js:
    print('shotsData found in JS')
    # find surrounding lines
    lines = js.split('\n')
    for i, line in enumerate(lines):
        if 'shotsData' in line:
            print(f'Line {i}: {line.strip()}')
            # print next few lines
            for j in range(i+1, min(i+5, len(lines))):
                print(f'  {lines[j].strip()}')
            break
else:
    print('shotsData not found in JS')

# Search for getMatchShots
if 'getMatchShots' in js:
    print('\ngetMatchShots found')
    # extract the URL pattern
    pattern = r'[\"\'](/main/getMatchShots[^\"\']+)[\"\']'
    matches = re.findall(pattern, js)
    for m in matches:
        print(f'  {m}')
else:
    print('\ngetMatchShots not found')

# Search for any /main/ endpoint
pattern2 = r'[\"\'](/main/[a-zA-Z]+)[\"\']'
matches2 = re.findall(pattern2, js)
if matches2:
    print('\n/main/ endpoints found:')
    for m in set(matches2):
        print(f'  {m}')

# Search for any API calls with match ID
pattern3 = r'[\"\'](https?://understat\.com/api/[^\"\']+)[\"\']'
matches3 = re.findall(pattern3, js)
if matches3:
    print('\nAPI endpoints:')
    for m in matches3:
        print(f'  {m}')