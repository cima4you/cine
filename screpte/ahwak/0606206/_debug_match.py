import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

def clean_title(t):
    t = re.sub(r'^مسلسل\s+', '', t)
    t = re.sub(r'\s+مترجم\s*$', '', t)
    t = re.sub(r'\s+مدبلج\s*$', '', t)
    t = re.sub(r'\s+مدبلجة\s*$', '', t)
    t = re.sub(r'\s+مترجمة\s*$', '', t)
    t = re.sub(r'\s*-\s*$', '', t)
    t = re.sub(r'\s*\(مترجم\)\s*$', '', t)
    t = re.sub(r'\s*\(مدبلج\)\s*$', '', t)
    if ' - ' in t:
        parts = t.split(' - ', 1)
        first = parts[0].strip()
        latin_count = sum(1 for c in first if c.isascii() and c.isalpha())
        arabic_count = sum(1 for c in first if '\u0600' <= c <= '\u06FF')
        if latin_count > arabic_count:
            t = first
        else:
            second = parts[1].strip()
            latin2 = sum(1 for c in second if c.isascii() and c.isalpha())
            arabic2 = sum(1 for c in second if '\u0600' <= c <= '\u06FF')
            if latin2 > arabic2:
                t = second
    return t.strip()

def norm(t):
    return re.sub(r'[\u064B-\u0652]', '', re.sub(r'\s+', '', (t or '').strip().lower()))

# Load existing completed data
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-completed.js', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'\[\s*\{', content, re.DOTALL)
start = m.start()
depth = 0
for i in range(start, len(content)):
    if content[i] == '[': depth += 1
    elif content[i] == ']':
        depth -= 1
        if depth == 0:
            existing = json.loads(content[start:i+1])
            break

# Clean existing titles
for x in existing:
    cleaned = clean_title(x.get('title', ''))
    if cleaned != x.get('title', ''):
        x['title'] = cleaned
exist_map = {norm(x.get('title', '')): x for x in existing}

# Load source
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_full.json', 'r', encoding='utf-8') as f:
    source = json.load(f)

# Check a few matching series
checked = 0
updated_servers = 0
no_servers = 0

for item in source:
    t = norm(clean_title(item.get('title', '')))
    if t in exist_map:
        checked += 1
        old_item = exist_map[t]
        # Check if any server update happened
        for s in item.get('seasons', []):
            sn = s.get('season', 0)
            for ep in s.get('episodes', []):
                ns = ep.get('servers', [])
                if ns:
                    # Try to find matching episode in old data
                    old_seasons = {s2.get('season', 0): s2 for s2 in old_item.get('seasons', [])}
                    if sn in old_seasons:
                        old_eps = {e.get('title', ''): e for e in old_seasons[sn].get('episodes', [])}
                        et = ep.get('title', '')
                        if et in old_eps:
                            os = old_eps[et].get('servers', [])
                            if ns != os:
                                updated_servers += 1
                        else:
                            no_servers += 1
                    else:
                        no_servers += 1
                else:
                    no_servers += 1

print(f"Matching series checked: {checked}")
print(f"Episodes where servers WOULD be updated: {updated_servers}")
print(f"Episodes where no update: {no_servers}")

# Also check first matching series
for item in source:
    t = norm(clean_title(item.get('title', '')))
    if t in exist_map:
        old_item = exist_map[t]
        print(f"\nFirst matching series: {item['title'][:50]}")
        print(f"  Existing title: {old_item['title'][:50]}")
        print(f"  Matched: {t}")
        # Compare first episode servers
        for s in item.get('seasons', []):
            sn = s.get('season', 0)
            for ep in s.get('episodes', [])[:1]:
                ns = ep.get('servers', [])
                old_seasons = {s2.get('season', 0): s2 for s2 in old_item.get('seasons', [])}
                if sn in old_seasons:
                    old_eps = {e2.get('title', ''): e2 for e2 in old_seasons[sn].get('episodes', [])}
                    et = ep.get('title', '')
                    if et in old_eps:
                        os = old_eps[et].get('servers', [])
                        print(f"  New servers: {json.dumps(ns[:2], ensure_ascii=False)}")
                        print(f"  Old servers: {json.dumps(os[:2] if os else [], ensure_ascii=False)}")
                        print(f"  Match (new!=old): {ns != os}")
        break
