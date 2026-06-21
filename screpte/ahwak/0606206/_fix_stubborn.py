import os, sys, json, re, urllib.request, time

sys.stdout.reconfigure(encoding='utf-8')
DATA_DIR = r'D:\web-secriping\Ancien PC\DT\site-rachid\data'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
DELAY = 1.5

def fetch(url):
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

def extract_servers_aggressive(html):
    sv = []
    # Try direct <li> with data-embed-url
    for m in re.finditer(r'<li[^>]*data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
        u, n = m.group(1), m.group(2).strip()
        if u and n:
            sv.append({'name': n, 'url': u, 'isDefault': len(sv) == 0})
    # Try any data-embed-url with <a><strong>
    if not sv:
        for m in re.finditer(r'data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
            u, n = m.group(1), m.group(2).strip()
            if u and n:
                sv.append({'name': n, 'url': u, 'isDefault': len(sv) == 0})
    # Try direct iframe
    if not sv:
        m = re.search(r'<iframe[^>]*src="([^"]+)"', html)
        if m:
            sv.append({'name': 'Vidspeeds', 'url': m.group(1), 'isDefault': True})
    # LAST RESORT: any data-embed-url in the entire HTML, even in JS
    if not sv:
        # Find unique embed URLs
        seen = set()
        for m in re.finditer(r'data-embed-url="(https?://[^"]+)"', html):
            u = m.group(1)
            if u not in seen and 'vidspeed' in u.lower():
                seen.add(u)
                sv.append({'name': 'Vidspeeds', 'url': u, 'isDefault': len(sv) == 0})
        for m in re.finditer(r'data-embed-url="(https?://[^"]+)"', html):
            u = m.group(1)
            if u not in seen:
                seen.add(u)
                sv.append({'name': f'Server {len(sv)+1}', 'url': u, 'isDefault': len(sv) == 0})
    return sv

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
    
    fixed = 0
    for item in items:
        for s in item.get('seasons', []):
            for e in s.get('episodes', []):
                sv = e.get('servers', [])
                if not sv:
                    continue
                if not (isinstance(sv, list) and len(sv) > 0 and isinstance(sv[0], dict) and sv[0].get('name') == 'watch'):
                    continue
                vid_url = sv[0].get('url', '')
                m2 = re.search(r'[?&]vid=([0-9a-fA-F]+)', vid_url)
                vid = m2.group(1) if m2 else None
                if not vid:
                    continue
                time.sleep(DELAY)
                html = fetch(f'https://yam.ahwaktv.net/see.php?vid={vid}')
                if not html:
                    continue
                servers = extract_servers_aggressive(html)
                if servers:
                    e['servers'] = servers
                    fixed += 1
                    print(f'  Fixed: {item.get("title","")} ep {e.get("episodeNumber","")} ({servers[0]["name"]})')
    
    print(f'{label}: fixed {fixed}')
    with open(path, 'w', encoding='utf-8') as f:
        lbl = 'منتهية' if 'completed' in fname else 'مستمرة'
        f.write(f'// مسلسلات تركية {lbl} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)

print('Done')
