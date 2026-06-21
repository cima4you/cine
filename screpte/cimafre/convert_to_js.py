import json, os, re

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MOVIES_FILE = os.path.join(DATA_DIR, 'arabic_movies.json')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
OUTPUT_JS = os.path.join(ROOT, 'data', 'data-cimafre.js')
OUTPUT_JSON = os.path.join(ROOT, 'data', 'data-cimafre.json')

movies = json.load(open(MOVIES_FILE, 'r', encoding='utf-8'))
valid = [m for m in movies if m.get('servers')]
print(f'Total: {len(movies)}, with servers: {len(valid)}')

for m in valid:
    t = m.get('title', '')
    t = re.sub(r'^مشاهدة (فيلم|مسلسل|انمي)\s+', '', t)
    t = re.sub(r'\s+كامل اون لاين.*', '', t)
    m['title_clean'] = t.strip() or t
    m['type'] = 'عربي'
    m['contentType'] = 'movie'

json.dump(valid, open(OUTPUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'JSON: {OUTPUT_JSON}')

with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
    f.write('const cd_cimafre = [\n')
    for m in valid:
        servers_json = json.dumps(m.get('servers', []), ensure_ascii=False)
        thumb = m.get('thumb_url') or m.get('thumb', '')
        dur = m.get('duration_str') or m.get('duration', '')
        f.write(f'  {{id:{json.dumps(m["vid"])}, title:{json.dumps(m.get("title_clean",""), ensure_ascii=False)}, servers:{servers_json}, poster:{json.dumps(thumb, ensure_ascii=False)}, thumb:{json.dumps(thumb, ensure_ascii=False)}, duration:{json.dumps(dur, ensure_ascii=False)}, type:"عربي", contentType:"movie"}},\n')
    f.write('];\n')

print(f'JS: {OUTPUT_JS} ({len(valid)} movies)')
total_sv = sum(len(m.get('servers', [])) for m in valid)
print(f'Total servers: {total_sv}')
