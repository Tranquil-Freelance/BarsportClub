#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re

url = "https://understat.com/league/Serie_A/2026"
resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
html = resp.text
soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')
for i, script in enumerate(scripts):
    if script.string:
        if 'datesData' in script.string:
            print(f'Script {i} contains datesData')
            # extract the line
            lines = script.string.split('\n')
            for line in lines:
                if 'datesData' in line:
                    print(line[:200])
                    # try to find JSON.parse
                    match = re.search(r"JSON\.parse\s*\(\s*'(.*?)'\s*\)", line)
                    if match:
                        print('Found JSON.parse')
        if 'var ' in script.string:
            # print all var names
            vars = re.findall(r'var\s+(\w+)\s*=', script.string)
            if vars:
                print(f'Script {i} vars: {vars}')
print('Total scripts:', len(scripts))
# Also search for other data variables
for script in scripts:
    if script.string and 'teamsData' in script.string:
        print('Found teamsData')
    if script.string and 'matchesData' in script.string:
        print('Found matchesData')
    if script.string and 'playersData' in script.string:
        print('Found playersData')