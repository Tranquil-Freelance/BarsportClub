import re
import sys
sys.path.insert(0, 'venv312/Lib/site-packages')
with open('venv312/Lib/site-packages/soccerdata/fbref.py', 'r', encoding='utf-8') as f:
    content = f.read()
    matches = re.findall(r'progressive', content, re.IGNORECASE)
    if matches:
        print('Found progressive')
        # print lines containing progressive
        for line in content.splitlines():
            if 'progressive' in line.lower():
                print(line[:200])
    else:
        print('No progressive')
    # also search for 'sca', 'shot_creating'
    for term in ['sca', 'shot_creating', 'shot creating', 'SCA']:
        for line in content.splitlines():
            if term.lower() in line.lower():
                print(line[:200])