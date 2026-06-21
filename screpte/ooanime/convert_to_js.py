import json, os, re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
SERIES_PATH = os.path.join(DATA_DIR, 'ooanime_series.json')
JS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'data-ooanime.js')
JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'data-ooanime.json')

with open(SERIES_PATH, 'r', encoding='utf-8') as f:
    series_list = json.load(f)

output = []
for s in series_list:
    if not s.get('seasons'):
        continue

    title = s.get('title', '').strip()
    if not title:
        continue

    categories = []
    if s.get('category'):
        categories.append(s['category'])

    seasons = []
    for si, sea in enumerate(s['seasons']):
        episodes = []
        ep_title_base = sea.get('title', f'الموسم {si+1}')
        ep_number = si + 1

        for ei, ep in enumerate(sea.get('episodes', [])):
            if not ep.get('video_url'):
                continue

            ep_name = ep.get('title', '')
            m = re.search(r'الحلقة[_\s]*(\d+)', ep_name)
            if not m:
                m = re.search(r'Ep(\d+)', ep.get('video_url', ''))
            ep_num = int(m.group(1)) if m else (ei + 1)
            ep_name_clean = f'الحلقة {ep_num}'

            episodes.append({
                'episodeNumber': ep_num,
                'title': ep_name_clean,
                'duration': '',
                'servers': [
                    {
                        'name': 'Ooanime',
                        'url': ep['video_url'],
                        'isDefault': True,
                    }
                ],
                'downloadServers': [],
            })

        if episodes:
            episodes.sort(key=lambda e: e['episodeNumber'])
            seasons.append({
                'seasonNumber': ep_number,
                'description': '',
                'poster': '',
                'episodes': episodes,
            })

    if not seasons:
        continue

    poster = s.get('poster', '')
    if poster and not poster.startswith('http'):
        poster = f'https://www.ooanime.com/{poster}'

    item = {
        'title': title,
        'year': s.get('year', ''),
        'rating': s.get('rating', ''),
        'type': 'كرتون',
        'contentType': 'series',
        'description': s.get('description', ''),
        'poster': poster,
        'categories': categories,
        'quality': 'HD',
        'badge': 'كرتون',
        'badgeClr': 'orange',
        'seasons': seasons,
    }
    output.append(item)

js = 'const cd_ooanime = ' + json.dumps(output, ensure_ascii=False) + ';\n'

os.makedirs(os.path.dirname(JS_PATH), exist_ok=True)
with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write(js)

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'Converted {len(output)} series to {JS_PATH}')
print(f'Total episodes: {sum(len(sea.get("episodes",[])) for s in output for sea in s.get("seasons",[]))}')
print(f'Total seasons: {sum(len(s.get("seasons",[])) for s in output)}')
