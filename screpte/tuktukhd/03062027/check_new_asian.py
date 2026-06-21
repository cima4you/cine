import json, re

with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

with open('scripts/tuktukhd/data/tuktuk_asian_index.json', 'r', encoding='utf-8') as f:
    asian_index = json.load(f)

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

existing = set()
for item in data:
    key = (norm(item.get('title','')), str(item.get('year','')))
    existing.add(key)

new_count = 0
existing_count = 0
new_movies = []
for m in asian_index:
    key = (norm(m['name']), m['year'])
    if key not in existing:
        new_count += 1
        new_movies.append(m)
    else:
        existing_count += 1

print('Total in Asian index: {}'.format(len(asian_index)))
print('Already in data.js: {}'.format(existing_count))
print('NEW (not in data.js): {}'.format(new_count))

if new_movies:
    print('\nSample new movies:')
    seen = set()
    for m in new_movies:
        k = (m['name'], m['year'])
        if k not in seen:
            seen.add(k)
            print('  "{}" ({})'.format(m['name'], m['year']))
            if len(seen) >= 15:
                break
