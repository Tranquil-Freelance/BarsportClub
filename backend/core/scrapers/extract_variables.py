#!/usr/bin/env python3
import json
import re
import sys

def extract_variables(html):
    # Find all script tags
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    variables = {}
    for script in scripts:
        if script.string is None:
            continue
        content = script.string
        # Pattern for var variable = JSON.parse('...');
        pattern = r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)\s*;'
        matches = re.findall(pattern, content, re.DOTALL)
        for var_name, encoded in matches:
            try:
                decoded = encoded.encode('utf-8').decode('unicode_escape')
                data = json.loads(decoded)
                variables[var_name] = data
                print(f"Found variable: {var_name} (type: {type(data).__name__})")
                if isinstance(data, list):
                    print(f"  Length: {len(data)}")
                    if len(data) > 0:
                        first = data[0]
                        if isinstance(first, dict):
                            print(f"  First item keys: {list(first.keys())}")
                elif isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())}")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                # maybe it's not JSON, store raw
                variables[var_name] = encoded
                print(f"Found variable: {var_name} (failed to decode)")
        # Also look for assignments like var x = {...} (without JSON.parse)
        # but ignore for now
    return variables

def main():
    with open('league.html', 'r', encoding='utf-8') as f:
        html = f.read()
    print("=== League page ===")
    vars1 = extract_variables(html)
    with open('team.html', 'r', encoding='utf-8') as f:
        html = f.read()
    print("=== Team page ===")
    vars2 = extract_variables(html)
    # Combine
    all_vars = {**vars1, **vars2}
    # Print summary
    print("\n=== Summary ===")
    for name, val in all_vars.items():
        if isinstance(val, (list, dict)):
            print(f"{name}: {type(val).__name__}")
            if isinstance(val, list):
                print(f"  length {len(val)}")
                # Try to find match IDs
                for item in val[:5]:
                    if isinstance(item, dict) and 'id' in item:
                        print(f"    id: {item['id']}")
                    if isinstance(item, dict) and 'match_id' in item:
                        print(f"    match_id: {item['match_id']}")
        else:
            print(f"{name}: {str(val)[:100]}")

if __name__ == '__main__':
    main()