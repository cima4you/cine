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

# Find "50 متر" in full.json
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_full.json', 'r', encoding='utf-8') as f:
    source = json.load(f)

print("=== Looking for 50 متر in full.json ===")
target = norm("50 متر")
found = None
for item in source:
    t = norm(clean_title(item.get('title', '')))
    if t == target:
        found = item
        break

if found:
    print(f"Found: {found['title']}")
    print(f"Seasons: {len(found.get('seasons', []))}")
    for s in found.get('seasons', []):
        eps = s.get('episodes', [])
        print(f"  Season {s.get('season')}: {len(eps)} eps")
        if eps:
            ep = eps[0]
            print(f"  First ep title: '{ep.get('title', '')[:50]}'")
            print(f"  First ep number: {ep.get('episodeNumber', ep.get('number', 'N/A'))}")
            sv = ep.get('servers', [])
            print(f"  Servers count: {len(sv)}")
            print(f"  Servers sample: {json.dumps(sv[:3], ensure_ascii=False)}")
else:
    print("NOT FOUND in full.json")

print()

# Find it in the formatted json too
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\ahwaktv_data_formatted.json', 'r', encoding='utf-8') as f:
    fmt_data = json.load(f)

print("=== Looking for 50 متر in ahwaktv_data_formatted.json ===")
found2 = None
for item in fmt_data:
    t = norm(clean_title(item.get('title', '')))
    if t == target:
        found2 = item
        break

if found2:
    print(f"Found: {found2['title']}")
    print(f"Seasons: {len(found2.get('seasons', []))}")
    for s in found2.get('seasons', []):
        eps = s.get('episodes', [])
        print(f"  Season {s.get('season')}: {len(eps)} eps")
        if eps:
            ep = eps[0]
            print(f"  First ep title: '{ep.get('title', '')[:50]}'")
            print(f"  Servers: {json.dumps(ep.get('servers', [])[:3], ensure_ascii=False)}")
else:
    print("NOT FOUND in formatted json")
