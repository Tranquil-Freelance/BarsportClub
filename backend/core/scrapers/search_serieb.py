import os
import site
import sys
for sitepack in site.getsitepackages():
    print("Searching", sitepack)
    for root, dirs, files in os.walk(sitepack):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        if 'Serie B' in f.read():
                            print(path)
                except:
                    pass