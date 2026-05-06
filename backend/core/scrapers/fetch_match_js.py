import requests
import re
url = 'https://understat.com/js/match.min.js?t=1765138215'
resp = requests.get(url)
js = resp.text
# search for patterns like /main/getMatchShots or /match/shotsData
patterns = [r'/main/getMatchShots', r'/match/shotsData', r'getMatchShots', r'shotsData']
for p in patterns:
    matches = re.findall(p, js)
    if matches:
        print(f'Found {len(matches)} matches for {p}')
        # show context
        lines = js.split('\n')
        for i, line in enumerate(lines):
            if p in line:
                print(f'Line {i}: {line.strip()[:200]}')
                break
# also look for AJAX calls
ajax_pattern = r'\.(?:ajax|post|get)\([^)]+["\'](/[^"\']+)["\']'
ajax_matches = re.findall(ajax_pattern, js, re.IGNORECASE)
if ajax_matches:
    print('AJAX endpoints:')
    for m in set(ajax_matches):
        print(' ', m)