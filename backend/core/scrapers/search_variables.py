#!/usr/bin/env python3
import re
import sys

def find_variables(html):
    # pattern for var variableName = JSON.parse('...');
    pattern = re.compile(r'var\s+(\w+)\s*=\s*JSON\.parse\s*\(\s*\'(.*?)\'\s*\)\s*;', re.DOTALL)
    matches = pattern.findall(html)
    for var_name, json_str in matches:
        print(f"Found variable: {var_name}")
        # decode unicode escapes
        try:
            decoded = json_str.encode('utf-8').decode('unicode_escape')
            # try to parse json
            import json
            data = json.loads(decoded)
            print(f"  Type: {type(data)}")
            if isinstance(data, list):
                print(f"  List length: {len(data)}")
                if data and isinstance(data[0], dict):
                    print(f"  First item keys: {list(data[0].keys())}")
            elif isinstance(data, dict):
                print(f"  Dict keys: {list(data.keys())}")
        except Exception as e:
            print(f"  Error decoding: {e}")
        print()
    # also look for var variableName = {...};
    pattern2 = re.compile(r'var\s+(\w+)\s*=\s*(\{.*?\})\s*;', re.DOTALL)
    for var_name, json_str in pattern2.findall(html):
        print(f"Found direct assignment: {var_name}")
        try:
            import json
            data = json.loads(json_str)
            print(f"  Type: {type(data)}")
        except:
            pass
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search_variables.py <html_file>")
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        html = f.read()
    find_variables(html)