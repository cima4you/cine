import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

# Find items with empty year that have (19xx) or (20xx) in title
for i, item in enumerate(data):
    y = item.get('year', '')
    title = item.get('title', '')
    if not y:
        m = re.search(r'\((\d{4})\)', title)
        if m:
            print('  Item %d: title="%s" -> extracted year %s from title' % (i, title[:80], m.group(1)))
            if i > 5:
                break

print('---')
# Also check all unique non-empty years that look unnatural
years = {}
for item in data:
    y = item.get('year', '')
    if y:
        years[y] = years.get(y, 0) + 1

import re
for y in sorted(years.keys()):
    if y and not re.match(r'^(19|20)\d{2}$', y):
        print('Unnatural year: %s (count: %d)' % (y, years[y]))
