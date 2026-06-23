import json, os, re, sys, time
sys.stdout.reconfigure(encoding='utf-8')

HINDI_JSON = os.path.join(os.path.dirname(__file__), 'hindi_movies.json')
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data-hindi.js')

if not os.path.exists(DATA_FILE):
    print(f'[data-hindi.js] Not found')
    sys.exit(1)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

arr_start = content.index('[')
arr_end = content.rindex(']') + 1
prefix = content[:arr_start]
suffix = content[arr_end:]

existing = json.loads(content[arr_start:arr_end])
for x in existing:
    x.setdefault('dateAdded', 0)

with open(HINDI_JSON, 'r', encoding='utf-8') as f:
    new_movies = json.load(f)

existing_titles = {m.get('title', '') for m in existing}
existing_by_title = {m.get('title', ''): m for m in existing}
added = 0
updated = 0
for m in new_movies:
    title = m.get('title', '')
    m['type'] = 'هندي'
    m['contentType'] = m.get('contentType', 'movie')
    if title not in existing_titles:
        m['dateAdded'] = int(time.time())
        existing.insert(0, m)
        existing_titles.add(title)
        added += 1
    else:
        old = existing_by_title[title]
        changed = False
        for key in ('servers', 'downloadServers', 'poster', 'rating', 'quality', 'duration', 'description', 'cast', 'categories'):
            if key in m and m[key] != old.get(key):
                old[key] = m[key]
                changed = True
        if changed:
            updated += 1

prefix = re.sub(r'— \d+ عنصر', f'— {len(existing)} عنصر', prefix)

with open(DATA_FILE, 'w', encoding='utf-8') as f:
    f.write(prefix + json.dumps(existing, ensure_ascii=False) + suffix)

print(f'[data-hindi.js] Added {added} new, updated {updated} — total: {len(existing)}')
