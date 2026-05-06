import requests
url = "https://understat.com/match/30116"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    # check if shotsData appears in HTML
    if 'shotsData' in resp.text:
        print("shotsData found in HTML")
    else:
        print("shotsData NOT found")
        # maybe the page is a redirect or error
        # print first 500 chars
        print(resp.text[:500])
else:
    print("Page not found")