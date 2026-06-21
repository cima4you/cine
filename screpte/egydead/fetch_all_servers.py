import sys, time, json, os, re
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://tv8.egydead.live'
INPUT = r'D:\Users\DT01\Desktop\rachid-site\scripts\egydead\egydead_all_raw.json'
OUTPUT_ENRICHED = r'D:\Users\DT01\Desktop\rachid-site\scripts\egydead\egydead_all_enriched.json'
OUTPUT_FORMATTED = r'D:\Users\DT01\Desktop\rachid-site\scripts\egydead\egydead_formatted.json'
import undetected_chromedriver as uc

def fetch_episode_servers(driver, url):
    """Fetch episode servers via POST View=1"""
    result = driver.execute_script(f'''
        return fetch('{url}', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
            body: 'View=1'
        }})
        .then(r => r.text())
        .then(html => ({{
            servers: (() => {{
                const sr = /<li[^>]*data-link="([^"]*)"[^>]*>.*?<p>([^<]*)<\\/p>/gs;
                const s = []; let m;
                while ((m = sr.exec(html)) !== null) s.push({{name: m[2], url: m[1]}});
                return s;
            }})(),
            description: (html.match(/<meta\\s+name="description"\\s+content="([^"]*)"/) || [])[1] || '',
            cover: (html.match(/singleCover[^>]*style="background-image:\\s*url\\(([^)]+)\\)/) || [])[1] || '',
            date: (html.match(/postDate[^>]*>([^<]+)</) || [])[1] || '',
            views: (html.match(/fa-eye<\\/i><em>(\\d+)<\\/em>/) || [])[1] || '',
            pageTitle: (html.match(/<title>([^<]+)<\\/title>/) || [])[1] || ''
        }}))
        .catch(e => ({{error: e.toString()}}));
    ''')
    return result

def parse_season_ep(ep):
    url = ep['url'].rstrip('/')
    slug = url.split('/')[-1]
    title = ep.get('title', '')
    season, episode = 1, 1
    m = re.search(r's(\d+)e(\d+)', slug, re.I)
    if m:
        season, episode = int(m.group(1)), int(m.group(2))
    else:
        m = re.search(r'-e(\d+)', slug)
        if m: episode = int(m.group(1))
    m = re.search(r'الجزء\s*(\w+)', title)
    if m:
        pw = m.group(1)
        pm = {'الاول':1,'الثاني':2,'الثالث':3,'الرابع':4,'الخامس':5}
        season = pm.get(pw, int(pw) if pw.isdigit() else season)
    m = re.search(r'الحلقة\s*(\d+)', title)
    if m: episode = int(m.group(1))
    m = re.search(r'الموسم\s*(\w+)', title)
    if m:
        pw = m.group(1)
        pm = {'الاول':1,'الثاني':2,'الثالث':3,'الرابع':4,'الخامس':5}
        season = pm.get(pw, int(pw) if pw.isdigit() else season)
    return season, episode

def extract_year(ep):
    text = (ep.get('description','') or '') + ' ' + (ep.get('title','') or '')
    for y in re.findall(r'\b(20\d{2})\b', text):
        if 2020 <= int(y) <= 2030: return y
    return ''

# Load existing data
with open(INPUT, 'r', encoding='utf-8') as f:
    episodes = json.load(f)

print(f'Loaded {len(episodes)} episodes')
need_servers = [e for e in episodes if not e.get('servers') or len(e.get('servers',[])) == 0]
have_servers = [e for e in episodes if e.get('servers') and len(e.get('servers',[])) > 0]
print(f'Need servers: {len(need_servers)}, Already have: {len(have_servers)}')

if not need_servers:
    print('All episodes already have servers!')
else:
    # Launch browser
    print('Launching browser...')
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(options=options, version_main=148)

    try:
        # Bypass Cloudflare
        print('Bypassing Cloudflare...')
        driver.get(f'{BASE_URL}/')
        time.sleep(25)

        # Fetch servers for each episode
        success = 0
        failed = 0
        for i, ep in enumerate(need_servers):
            url = ep['url']
            print(f'  [{i+1}/{len(need_servers)}] {ep.get("title","")[:50]}...', end=' ')
            
            data = fetch_episode_servers(driver, url)
            
            if 'error' not in data and data.get('servers'):
                ep['servers'] = data['servers']
                ep['description'] = ep.get('description') or data.get('description', '')
                ep['cover'] = ep.get('cover') or data.get('cover', '')
                ep['date'] = ep.get('date') or data.get('date', '')
                ep['views'] = ep.get('views') or data.get('views', '')
                success += 1
                print(f'{len(data["servers"])} servers ✅')
            elif 'error' not in data:
                ep['servers'] = []
                ep['description'] = ep.get('description') or data.get('description', '')
                print('0 servers ⚠️')
            else:
                failed += 1
                print(f'ERROR {data.get("error","")[:50]} ❌')
            
            time.sleep(0.5)
        
        print(f'\nDone: {success} with servers, {failed} failed')
    finally:
        driver.quit()

# Save enriched data
with open(OUTPUT_ENRICHED, 'w', encoding='utf-8') as f:
    json.dump(episodes, f, ensure_ascii=False, indent=2)
print(f'Saved: {OUTPUT_ENRICHED}')

# === Convert to formatted output ===
# Group by base series name
def clean_name(name):
    name = re.sub(r'\s+الجزء\s+\w+$', '', name)
    name = re.sub(r'\s+الموسم\s+\w+$', '', name)
    name = re.sub(r'\s+\d{4}\s+مترجم\s+و\s*$', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

series_map = {}
for ep in episodes:
    base = clean_name(ep.get('series_name', ''))
    if base not in series_map: series_map[base] = []
    series_map[base].append(ep)

# Deduplicate
for k in series_map:
    seen = set()
    series_map[k] = [e for e in series_map[k] if not (e['url'] in seen or seen.add(e['url']))]

# Build output
output = []
for base_name, eps in sorted(series_map.items()):
    first = next((e for e in eps if e.get('description')), eps[0])
    year = extract_year(first)
    
    seasons_dict = {}
    for ep in eps:
        sn, en = parse_season_ep(ep)
        if sn not in seasons_dict: seasons_dict[sn] = []
        ep_entry = {
            'episodeNumber': en,
            'title': ep.get('title', ''),
            'duration': '',
            'servers': [],
            'downloadServers': []
        }
        sv = ep.get('servers', [])
        for i, s in enumerate(sv):
            ep_entry['servers'].append({
                'name': f'server{i+1}',
                'url': s.get('url', ''),
                'isDefault': i == 0
            })
        seasons_dict[sn].append(ep_entry)
    
    for sn in seasons_dict:
        seasons_dict[sn].sort(key=lambda x: x['episodeNumber'])
    
    series_entry = {
        'title': base_name,
        'originalName': '',
        'year': year,
        'rating': '',
        'type': 'تركي',
        'contentType': 'series',
        'description': (first.get('description') or '')[:500],
        'cast': [],
        'poster': first.get('cover') or first.get('image', ''),
        'categories': ['مسلسلات تركية'],
        'quality': 'HD' if 'HD' in (first.get('description','') or '').upper() else 'متعدد',
        'seasons': []
    }
    for sn in sorted(seasons_dict.keys()):
        series_entry['seasons'].append({
            'seasonNumber': sn,
            'trial': '',
            'description': '',
            'poster': '',
            'episodes': seasons_dict[sn]
        })
    output.append(series_entry)

with open(OUTPUT_FORMATTED, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# Stats
total_eps = sum(len(se['episodes']) for s in output for se in s['seasons'])
total_srv = sum(len(ep['servers']) for s in output for se in s['seasons'] for ep in se['episodes'])
print(f'\nFinal: {len(output)} series, {total_eps} episodes, {total_srv} server links')
print(f'Output: {OUTPUT_FORMATTED}')
