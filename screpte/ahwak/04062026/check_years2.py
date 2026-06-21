import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

# Find ALL items with empty year that have (19xx) or (20xx) in title
found = []
for i, item in enumerate(data):
    y = item.get('year', '')
    title = item.get('title', '')
    if not y:
        m = re.search(r'\((\d{4})\)', title)
        if m:
            found.append((i, title[:80], m.group(1)))

print('Items with empty year but year in title (%d total):' % len(found))
for i, t, y in found[:20]:
    print('  Item %d: "%s" -> year=%s' % (i, t, y))
print('...')
if len(found) > 20:
    print('  (%d more)' % (len(found)-20))

# Also check items where year field has a year but title has a DIFFERENT year
diff = []
for i, item in enumerate(data):
    y = item.get('year', '')
    title = item.get('title', '')
    if y:
        m = re.search(r'\((\d{4})\)', title)
        if m and m.group(1) != y:
            diff.append((i, title[:80], y, m.group(1)))

print('\nItems with year field != year in title (%d total):' % len(diff))
for i, t, yf, yt in diff[:20]:
    print('  Item %d: "%s" -> field_year=%s, title_year=%s' % (i, t, yf, yt))
