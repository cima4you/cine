import json, os, re, sys, time
sys.stdout.reconfigure(encoding='utf-8')

TURKISH_JSON = r"screpte\tuktukhd\tuktuk\turkish_movies.json"
DATA_FILE = r"data-turkish-movies.js"

if not os.path.exists(DATA_FILE):
    print(f'[data-turkish-movies.js] Not found — creating new file')
    content = '// أفلام تركية — 0 عنصر\nconst cd_turkish_movies = [];'
else:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

arr_start = content.index('[')
arr_end = content.rindex(']') + 1
prefix = content[:arr_start]
suffix = content[arr_end:]

existing = json.loads(content[arr_start:arr_end])
for x in existing:
    x.setdefault('dateAdded', 0)

with open(TURKISH_JSON, 'r', encoding='utf-8') as f:
    new_movies = json.load(f)

existing_titles = {m.get('title', '') for m in existing}
existing_by_title = {m.get('title', ''): m for m in existing}
added = 0
updated = 0
for m in new_movies:
    title = m.get('title', '')
    m['type'] = 'تركي'
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

print(f'[data-turkish-movies.js] Added {added} new, updated {updated} — total: {len(existing)}')
