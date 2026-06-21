import os, sys, json, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')
DATA_DIR = r'D:\web-secriping\Ancien PC\DT\site-rachid\data'
BASE_URL = 'https://yam.ahwaktv.net'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
DELAY = 0.3

def fetch(url):
    import urllib.request
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=20)
            return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            return None

def extract_vid(url):
    m = re.search(r'[?&]vid=([0-9a-fA-F]+)', url)
    return m.group(1) if m else ''

def extract_servers(html):
    servers = []
    for m in re.finditer(r'<li[^>]*data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
        url = m.group(1)
        name = m.group(2).strip()
        if url and name:
            servers.append({'name': name, 'url': url, 'isDefault': len(servers) == 0})
    if not servers:
        for m in re.finditer(r'data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
            url = m.group(1)
            name = m.group(2).strip()
            if url and name:
                servers.append({'name': name, 'url': url, 'isDefault': len(servers) == 0})
    vidspeed = [s for s in servers if 'vidspeed' in s['name'].lower() or 'vidspeed' in s['url'].lower()]
    others = [s for s in servers if s not in vidspeed]
    servers = vidspeed + others
    for i, s in enumerate(servers):
        s['isDefault'] = (i == 0)
    return servers

def is_placeholder(ep):
    sv = ep.get('servers', [])
    if not sv:
        return True
    if isinstance(sv, list) and len(sv) > 0:
        first = sv[0]
        if isinstance(first, dict) and first.get('name') == 'watch' and 'watch.php' in first.get('url', ''):
            return True
    return False

def fix_episode(ep):
    url = ep.get('url', '')
    # Also check servers for watch.php url
    sv = ep.get('servers', [])
    if sv and isinstance(sv, list) and len(sv) > 0:
        first = sv[0]
        if isinstance(first, dict) and 'watch.php' in first.get('url', ''):
            url = first['url']
    if not url or 'watch.php' not in url:
        return False
    vid = extract_vid(url)
    if not vid:
        return False
    time.sleep(DELAY)
    html = fetch(f'{BASE_URL}/see.php?vid={vid}')
    if not html:
        return False
    servers = extract_servers(html)
    if servers:
        ep['servers'] = servers
        return True
    return False

def load_js(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'(const|let|var)\s+(\w+)\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
    items = json.loads(m.group(2)) if m else []
    return items, m.group(2), m.start(2) if m else 0

def save_js(path, items, start_pos, var_name, label):
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()
    new_json = json.dumps(items, ensure_ascii=False)
    new_content = original[:start_pos] + new_json + original[original.find('];', start_pos) + 2:] if '];' in original[start_pos:] else original[:start_pos] + f'const {var_name} = ' + new_json + ';'
    # Simpler: just rewrite the whole file
    lbl = 'منتهية' if 'completed' in path else 'مستمرة'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات تركية {lbl} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)

def process_file(path, label, workers=6):
    items, var_name, start_pos = load_js(path)
    if not items:
        print(f'❌ {label}: لا توجد بيانات')
        return
    
    # Collect all placeholder episodes
    todo = []
    for si, item in enumerate(items):
        for sj, s in enumerate(item.get('seasons', [])):
            for ek, e in enumerate(s.get('episodes', [])):
                if is_placeholder(e):
                    todo.append((si, sj, ek, e))
    
    print(f'{label}: {len(items)} series, {len(todo)} episodes with placeholder servers')
    if not todo:
        return
    
    fixed = 0
    errors = 0
    
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {}
        for si, sj, ek, e in todo:
            futs[ex.submit(fix_episode, e)] = e
        
        for f in as_completed(futs):
            e = futs[f]
            try:
                if f.result():
                    fixed += 1
                else:
                    errors += 1
            except:
                errors += 1
            if (fixed + errors) % 50 == 0:
                print(f'  📡 {fixed} fixed, {errors} errors / {len(todo)}')
    
    print(f'  ✅ {label}: fixed {fixed}, errors {errors}')
    save_js(path, items, start_pos, var_name, label)
    print(f'  💾 Saved: {path}')

if __name__ == '__main__':
    for fname, label in [
        ('data-turkish-completed.js', 'المكتملة'),
        ('data-turkish-ongoing.js', 'المستمرة'),
    ]:
        process_file(os.path.join(DATA_DIR, fname), label)
    print('\n🎉 Done')
