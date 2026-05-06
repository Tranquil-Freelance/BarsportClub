import re
import json
import sys
sys.path.insert(0, '.')
from app.scraper.understat_parser import extract_json_from_script

with open('backend/imports/Cagliari 1 - 2 Como.html', 'r', encoding='utf-8') as f:
    html = f.read()

# try to extract matchData
try:
    data = extract_json_from_script(html, 'matchData')
    print("matchData found:", json.dumps(data, indent=2)[:500])
except ValueError as e:
    print("matchData not found via extract_json_from_script:", e)
    # manual search
    pattern = r"var\s+matchData\s*=\s*JSON\.parse\s*\(\s*'(.*?)'\s*\)\s*;"
    match = re.search(pattern, html, re.DOTALL)
    if match:
        encoded = match.group(1)
        decoded = encoded.encode('utf-8').decode('unicode_escape')
        data = json.loads(decoded)
        print("matchData found via regex:", json.dumps(data, indent=2)[:500])
    else:
        print("matchData not found in HTML")

# also search for shotsData
try:
    shots = extract_json_from_script(html, 'shotsData')
    print("shotsData found:", json.dumps(shots, indent=2)[:500])
except ValueError as e:
    print("shotsData not found:", e)