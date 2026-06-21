import re, json, sys, os

sys.stdout.reconfigure(encoding='utf-8')

BASE = r'D:\Users\DT01\Desktop\rachid-site'
path = os.path.join(BASE, r'test\data.js')

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Sample entries with bad years
bad_years = ['8217', '8211', '8216', '8230', '2073', '2039']
for y in bad_years:
    pat = re.compile(r'"year":\s*"' + y + r'".*?"title":\s*"([^"]+)"', re.DOTALL)
    m = pat.search(content)
    if m:
        title = m.group(1)
        yr = re.search(r'\b(19\d{2}|20[0-2]\d)\b', title)
        print(f'{y}: "{title[:80]}" -> year in title: {yr.group(0) if yr else "None"}')
    else:
        print(f'{y}: not found')
