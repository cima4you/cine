#!/usr/bin/env python3
"""
Process AhwakTV series data:
1. Merge multi-season series (same base name, e.g. "اخوتى" + "مسلسل إخوتى 2")
2. Detect completed series (episode title contains "والاخيرة")
3. Categorize into completed / ongoing
4. Generate data.js with proper contentType, seasons, and isComplete flag
"""
import json, re, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, 'ahwaktv_data.json')
OUTPUT_PATH = os.path.join(SCRIPT_DIR, '..', '..', 'data.js')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    raw_series = json.load(f)

# ─────────── Step 1: Normalize names ───────────
def normalize(name):
    """Normalize name for matching: remove prefix, normalize alef, strip trailing words/numbers"""
    n = name.strip()
    if n.startswith('مسلسل '):
        n = n[5:].strip()
    # Normalize alef variants
    n = n.replace('\u0625', '\u0627')  # إ → ا
    n = n.replace('\u0623', '\u0627')  # أ → ا
    n = n.replace('\u0622', '\u0627')  # آ → ا
    # Remove trailing " مترجم" or " مدبلج"
    n = re.sub(r'\s+(مترجم|مدبلج)\s*$', '', n).strip()
    # Remove trailing " N" where N is a season number (2-9)
    m = re.match(r'^(.*?)\s+([2-9])$', n)
    if m:
        return m.group(1).strip()
    return n

def get_season_num(name):
    """Extract season number from name, default 1"""
    n = name.strip()
    if n.startswith('مسلسل '):
        n = n[5:].strip()
    m = re.match(r'^(.*?)\s+([2-9])$', n)
    if m:
        return int(m.group(2))
    return 1

# ─────────── Step 2: Group by normalized name ───────────
groups = {}
for s in raw_series:
    base = normalize(s['name'])
    if base not in groups:
        groups[base] = []
    groups[base].append(s)

print(f'Total raw series: {len(raw_series)}')
print(f'Unique base names: {len(groups)}')

# Find multi-series groups
multi = {k: v for k, v in groups.items() if len(v) > 1}
print(f'Multi-series groups: {len(multi)}')
for base, series_list in multi.items():
    print(f'  "{base}": {[(s["name"], len(s["episodes"])) for s in series_list]}')

# ─────────── Step 3: Merge multi-season series ───────────
merged_series = []
for base, series_list in groups.items():
    if len(series_list) == 1:
        s = series_list[0]
        # Check for completed
        eps = s.get('episodes', [])
        is_complete = False
        if eps:
            last_ep = eps[-1]
            if 'والاخيرة' in last_ep.get('title', ''):
                is_complete = True
        merged_series.append({
            'name': base,
            'poster': s['poster'],
            'description': s['description'],
            'series_url': s.get('series_url', ''),
            'episodes': eps,
            'isComplete': is_complete
        })
    else:
        # Merge: use the first series as base, add others as later seasons
        # Sort by season number
        series_list.sort(key=lambda s: get_season_num(s['name']))
        base_series = series_list[0]
        all_eps = []
        max_num = 0
        season_offset = 0
        for si, s in enumerate(series_list):
            season_num = get_season_num(s['name'])
            eps = s.get('episodes', [])
            for ep in eps:
                all_eps.append({
                    'number': ep['number'],
                    'title': ep['title'],
                    'url': ep['url'],
                    'vid': ep.get('vid', ''),
                    'servers': ep.get('servers', []),
                    'season': season_num
                })
                if ep['number'] > max_num:
                    max_num = ep['number']
        all_eps.sort(key=lambda e: (e['season'], e['number']))
        
        # Detect completed
        is_complete = False
        if all_eps:
            last_ep = all_eps[-1]
            if 'والاخيرة' in last_ep.get('title', ''):
                is_complete = True
        
        merged_series.append({
            'name': base,
            'poster': base_series['poster'],
            'description': base_series['description'],
            'series_url': base_series.get('series_url', ''),
            'episodes': all_eps,
            'isComplete': is_complete
        })

# ─────────── Step 4: Separate completed / ongoing ───────────
completed = [s for s in merged_series if s['isComplete']]
ongoing = [s for s in merged_series if not s['isComplete']]

print(f'\nMerged series: {len(merged_series)}')
print(f'Completed: {len(completed)}')
print(f'Ongoing: {len(ongoing)}')

print(f'\nCompleted series:')
for s in completed:
    print(f'  {s["name"]} ({len(s["episodes"])} eps)')

# ─────────── Step 5: Build contentData format ───────────
def build_seasons(eps):
    """Convert flat episode list (with season field) to seasons array"""
    if not eps:
        return []
    # Check if we have multi-season data
    seasons_in_eps = set(e.get('season', 1) for e in eps)
    if len(seasons_in_eps) == 1:
        # Single season
        return [{
            'season': 1,
            'episodes': [{
                'number': e['number'],
                'title': e['title'],
                'servers': e.get('servers', [{'name': 'watch', 'url': e['url'], 'isDefault': True}]),
                'downloadServers': [{'name': 'رابط المشاهدة', 'url': e['url']}]
            } for e in eps]
        }]
    else:
        # Multiple seasons
        seasons_map = {}
        for e in eps:
            sn = e.get('season', 1)
            if sn not in seasons_map:
                seasons_map[sn] = []
            seasons_map[sn].append(e)
        return [{
            'season': sn,
            'episodes': [{
                'number': e['number'],
                'title': e['title'],
                'servers': e.get('servers', [{'name': 'watch', 'url': e['url'], 'isDefault': True}]),
                'downloadServers': [{'name': 'رابط المشاهدة', 'url': e['url']}]
            } for e in sorted(eps_list, key=lambda x: x['number'])]
        } for sn, eps_list in sorted(seasons_map.items())]

content_data = []
for s in merged_series:
    seasons = build_seasons(s['episodes'])
    content_data.append({
        'title': s['name'],
        'poster': s['poster'],
        'description': s['description'],
        'year': '',
        'type': 'تركي',
        'contentType': 'series',
        'isComplete': s['isComplete'],
        'seasons': seasons
    })

# Also add completed series count
total_completed = sum(1 for c in content_data if c['isComplete'])
total_ongoing = len(content_data) - total_completed

print(f'\nFinal: {len(content_data)} series ({total_completed} completed, {total_ongoing} ongoing)')

# ─────────── Step 6: Load existing data.js and merge ───────────
# Read existing data.js to get non-series entries (movies)
existing_js_path = os.path.join(SCRIPT_DIR, '..', '..', 'data.js')
with open(existing_js_path, 'r', encoding='utf-8') as f:
    existing_js = f.read()

# Extract existing contentData
m = re.search(r'const contentData\s*=\s*(\[.*?\])\s*;', existing_js, re.DOTALL)
if m:
    existing_content = json.loads(m.group(1))
else:
    print('ERROR: Could not parse existing data.js')
    sys.exit(1)

# Keep movies from current data (non-series entries)
movies = [item for item in existing_content if item.get('contentType') != 'series']

# Read backup data.js for non-Turkish series and missing Arabic movies
BACKUP_PATH = os.path.join(SCRIPT_DIR, '..', '..', 'data.js.backup')
non_turkish_series = []
arabic_movies_restored = []
if os.path.exists(BACKUP_PATH):
    with open(BACKUP_PATH, 'r', encoding='utf-8') as f:
        backup_js = f.read()
    m = re.search(r'const contentData\s*=\s*(\[.*?\])\s*;', backup_js, re.DOTALL)
    if m:
        backup_content = json.loads(m.group(1))
        non_turkish_series = [item for item in backup_content
                              if item.get('contentType') == 'series'
                              and (item.get('type') or '').strip() != 'تركي']
        print(f'Non-Turkish series from backup: {len(non_turkish_series)}')

        # Restore Arabic movies (type=عربي, contentType=movie) missing from current data
        existing_titles = set((item.get('title') or '').strip() for item in existing_content)
        for item in backup_content:
            if (item.get('type') or '').strip() == 'عربي' and item.get('contentType') == 'movie':
                title = (item.get('title') or '').strip()
                if title not in existing_titles:
                    arabic_movies_restored.append(item)
        print(f'Arabic movies restored from backup: {len(arabic_movies_restored)}')
    else:
        print('WARNING: Could not parse backup data.js')
else:
    print('WARNING: No backup file found at', BACKUP_PATH)

# Keep only non-Turkish-series entries from existing (movies)
other_content = [item for item in existing_content if item.get('contentType') != 'series']

print(f'Existing movies: {len(other_content)}')
print(f'New Turkish series: {len(content_data)}')

# Combine: movies + restored non-Turkish series + restored Arabic movies + Turkish series
final_content = movies + non_turkish_series + arabic_movies_restored + content_data

# ─────────── Step 7: Write data.js ───────────
json_str = json.dumps(final_content, ensure_ascii=False)

output = f'\t\t\t\t\tconst contentData = {json_str};'

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(output)

print(f'\nWritten {OUTPUT_PATH}')
print(f'Total entries: {len(final_content)} ({len(movies)} movies, {len(non_turkish_series)} non-Turkish series, {len(arabic_movies_restored)} Arabic movies restored, {len(content_data)} Turkish series)')
