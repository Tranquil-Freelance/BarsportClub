import requests
import re

match_id = 27362
url = f'https://understat.com/match/{match_id}'
headers = {'User-Agent': 'Mozilla/5.0'}
resp = requests.get(url, headers=headers)
html = resp.text
# find all script src
script_srcs = re.findall(r'<script[^>]+src="([^"]+)"', html)
print('Script srcs:')
for src in script_srcs:
    print(' ', src)
# find all URLs in JavaScript
url_pattern = r'[\"\'](https?://[^\"\']+?\.json[^\"\']*?)[\"\']'
json_urls = re.findall(url_pattern, html)
print('JSON URLs:')
for u in json_urls:
    print(' ', u)
# find any API-like endpoints
api_pattern = r'[\"\'](/[^\"\']*(?:shots|match|data|get)[^\"\']*)[\"\']'
api_endpoints = set(re.findall(api_pattern, html))
print('API-like endpoints:')
for e in api_endpoints:
    if 'css' not in e and 'png' not in e:
        print(' ', e)