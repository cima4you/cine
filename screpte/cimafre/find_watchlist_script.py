import re, json

t = open('screpte/cimafre/data/detail.html', 'r', encoding='utf-8').read()

# Find the inline script that has the WatchList handler and load_stream
scripts = re.findall(r'<script[^>]*>(.*?)</script>', t, re.DOTALL)
for i, s in enumerate(scripts):
    if 'WatchList' in s or 'load_stream' in s:
        print(f'=== Script {i} ({len(s)} chars) ===')
        print(s)
        print()

# Also look for any data in the HTML that resembles server info
# Maybe search around the WatchList-like div structure
lines = t.split('\n')
for j, line in enumerate(lines):
    if 'سيرفر' in line or 'جودة' in line or 'watch' in line.lower():
        print(f'Line {j}: {line.strip()[:200]}')
