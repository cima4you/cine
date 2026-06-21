import os, sys, json, re, time

sys.stdout.reconfigure(encoding='utf-8')
DATA_DIR = r'D:\web-secriping\Ancien PC\DT\site-rachid\data'
BASE_URL = 'https://yam.ahwaktv.net'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

def norm(t):
    t = re.sub(r'\s+', '', (t or '').strip().lower())
    t = re.sub(r'[\u064B-\u0652]', '', t)
    t = re.sub(r'(الجزء|الموسم)\s*(الأول|الاول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+)', '', t)
    return t

def load_js(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
    items = json.loads(m.group(2)) if m else []
    return items, m.group(1) if m else 'cd_data'

def save_js(path, items, var_name):
    lbl = 'منتهية' if 'completed' in path else 'مستمرة'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات تركية {lbl} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)

# Load turkish_series_full.json and convert to site format
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_turkish_series import to_site_format, load_json

script_dir = os.path.dirname(os.path.abspath(__file__))
full = load_json(os.path.join(script_dir, 'data', 'turkish_series_full.json'))
print(f'📂 Full JSON: {len(full)} series')

converted = to_site_format(full)
print(f'🔄 Converted: {len(converted)} series')

# Build map by normalized title (stripping season/part suffixes)
full_map = {}
for item in converted:
    key = norm(item.get('title', ''))
    if key:
        full_map[key] = item

print(f'🗺 Map: {len(full_map)} unique normalized titles')

# Process each JS file
for fname, label in [
    ('data-turkish-completed.js', 'المكتملة'),
    ('data-turkish-ongoing.js', 'المستمرة'),
]:
    path = os.path.join(DATA_DIR, fname)
    items, var_name = load_js(path)
    updated = 0
    added_season = 0
    
    for item in items:
        item_key = norm(item.get('title', ''))
        if not item_key or item_key not in full_map:
            continue
        
        src = full_map[item_key]
        
        # Update poster/description if missing
        for key in ('poster', 'description'):
            if key in src and src[key] and not item.get(key):
                item[key] = src[key]
        
        # Update servers in episodes
        src_seasons = {}
        for s in src.get('seasons', []):
            sn = s.get('seasonNumber', s.get('season', 0))
            src_seasons[sn] = {e.get('title', ''): e for e in s.get('episodes', [])}
        
        for s in item.get('seasons', []):
            sn = s.get('seasonNumber', s.get('season', 0))
            if sn in src_seasons:
                src_eps = src_seasons[sn]
                for e in s.get('episodes', []):
                    et = e.get('title', '')
                    if et in src_eps:
                        ns = src_eps[et].get('servers', [])
                        os_ = e.get('servers', [])
                        if ns and ns != os_:
                            e['servers'] = ns
                            updated += 1
        
        # Also add seasonNumber to season if missing
        for s in item.get('seasons', []):
            if not s.get('seasonNumber') and s.get('season'):
                s['seasonNumber'] = s['season']
            elif not s.get('season') and s.get('seasonNumber'):
                s['season'] = s['seasonNumber']
    
    print(f'{label}: {updated} episodes updated ({len(items)} series)')
    save_js(path, items, var_name)
    print(f'  💾 Saved: {path}')

print('\n✅ Done')
