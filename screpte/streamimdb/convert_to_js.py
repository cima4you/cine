import json, os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
INPUT_PATH = os.path.join(DATA_DIR, 'streamimdb_movies.json')
OUTPUT_PATH = 'data/data-streamimdb.js'

with open(INPUT_PATH, 'r', encoding='utf-8') as f:
    movies = json.load(f)

entries = []
for m in movies:
    server_url = m.get('watch_server_url') or f'https://streamimdb.ru/embed/movie/{m["slug"].split("-")[0]}'

    entry = {
        'title': m['title'],
        'year': m.get('year', ''),
        'type': 'StreamIMDb',
        'contentType': m.get('contentType', 'movie'),
        'poster': m.get('poster', ''),
        'servers': [
            {'name': 'StreamIMDb', 'url': server_url, 'isDefault': True}
        ],
    }
    entries.append(entry)

output = f'// StreamIMDb - {len(entries)} films\n'
output += 'const cd_streamimdb = '
output += json.dumps(entries, ensure_ascii=False, indent=2)
output += ';\n'

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(output)

print(f'Saved {len(entries)} entries to {OUTPUT_PATH}')
