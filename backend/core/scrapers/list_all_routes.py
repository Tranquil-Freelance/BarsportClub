import urllib.request
import json

url = 'http://localhost:8000/openapi.json'
with urllib.request.urlopen(url) as f:
    data = json.load(f)
    for path in data.get('paths', {}):
        print(path)