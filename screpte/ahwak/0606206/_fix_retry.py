import os, sys, json, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')
DATA_DIR = r'D:\web-secriping\Ancien PC\DT\site-rachid\data'
BASE_URL = 'https://yam.ahwaktv.net'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
DELAY = 1.0  # longer delay to avoid rate limiting

def fetch(url):
    import urllib.request
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=30)
            return resp.read().decode('utf-8', errors='replace')
        except:
            if attempt < 2:
                time.sleep(5)
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
    vsp = [s for s in servers if 'vidspeed' in s['name'].lower() or 'vidspeed' in s['url'].lower()]
    others = [s for s in servers if s not in vsp]
    servers = vsp + others
    for i, s in enumerate(servers):
        s['isDefault'] = (i == 0)
    return servers

def needs_fix(ep):
    sv = ep.get('servers', [])
    if not sv:
        return True
    if isinstance(sv, list) and len(sv) > 0:
        first = sv[0]
        if isinstance(first, dict) and first.get('name') == 'watch' and 'watch.php' in first.get('url', ''):
            return True
    return False

def fix_episode(ep):
    sv = ep.get('servers', [])
    if not sv:
        return False
    for s in sv:
        if isinstance(s, dict):
            u = s.get('url', '')
            if 'watch.php' in u:
                vid = extract_vid(u)
                break
    else:
        return False
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

for fname, label in [
    ('data-turkish-completed.js', 'المكتملة'),
    ('data-turkish-ongoing.js', 'المستمرة'),
]:
    path = os.path.join(DATA_DIR, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'const (\w+) = (\[)', content)
    start = m.start(2)
    depth = 0
    for i in range(start, len(content)):
        ch = content[i]
        if ch == '[': depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                items = json.loads(content[start:i+1])
                var_name = m.group(1)
                break
    
    todo = []
    for si, item in enumerate(items):
        for sj, s in enumerate(item.get('seasons', [])):
            for ek, e in enumerate(s.get('episodes', [])):
                if needs_fix(e):
                    todo.append((si, sj, ek, e))
    
    print(f'{label}: {len(todo)} still need fixing')
    if not todo:
        continue
    
    fixed = 0
    errors = 0
    with ThreadPoolExecutor(max_workers=3) as ex:
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
            if (fixed + errors) % 25 == 0:
                print(f'  📡 {fixed} fixed, {errors} errors / {len(todo)}')
    
    print(f'  ✅ {label}: fixed {fixed}, errors {errors}')
    
    lbl = 'منتهية' if 'completed' in fname else 'مستمرة'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات تركية {lbl} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)

print('\n🎉 Done')
