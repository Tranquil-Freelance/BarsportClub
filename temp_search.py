import sys
sys.path.append('.')
with open('backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'include_router' in line:
            print(f'{i+1}: {line.strip()}')
        if 'scraper_router' in line or 'meritometro_router' in line:
            print(f'{i+1}: {line.strip()}')