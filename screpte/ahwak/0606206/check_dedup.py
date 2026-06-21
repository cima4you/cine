import json, re
with open('data/turkish_series_listing.json','r',encoding='utf-8') as f:
    data = json.load(f)

def clean_title(t):
    t = re.sub(r'^مسلسل\s+','',t)
    t = re.sub(r'\s+مترجم\s*$','',t)
    t = re.sub(r'\s+مدبلج\s*$','',t)
    t = re.sub(r'\s+مدبلجة\s*$','',t)
    t = re.sub(r'\s+مترجمة\s*$','',t)
    t = re.sub(r'\s*-\s*$','',t)
    return t.strip()

def extract_series_name(title):
    t = clean_title(title)
    t = re.sub(r'\s*الحلقة\s*\d+.*$','',t).strip()
    t = re.sub(r'\s+\d+\s*$','',t).strip()
    return t

def arabic_only(t):
    return re.sub(r'[a-zA-Z\s]', '', t).strip()

# Group by dedup_key
groups = {}
for item in data:
    series = extract_series_name(item['title'])
    key = arabic_only(series) or series or item.get('url','')
    groups.setdefault(key, []).append(item)

for key, group in sorted(groups.items()):
    print(f'[{len(group)}x] {key}:')
    for item in group:
        m = re.search(r'الحلقة\s*(\d+)', item['title'])
        ep = int(m.group(1)) if m else 0
        print(f'     ep={ep:3d} | {item["title"][:50]}')
