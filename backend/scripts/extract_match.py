#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')
from scripts.import_match_html import extract_variable, extract_match_info, extract_shots_data

html_path = 'backend/imports/Cagliari 1 - 2 Como.html'
html = open(html_path, encoding='utf-8').read()

try:
    match_info = extract_match_info(html)
    print('Match info:', match_info)
except Exception as e:
    print('Error extracting match info:', e)

try:
    shots_data = extract_shots_data(html)
    print('Shots data keys:', shots_data.keys())
    print('Home shots:', len(shots_data['h']))
    print('Away shots:', len(shots_data['a']))
except Exception as e:
    print('Error extracting shots data:', e)