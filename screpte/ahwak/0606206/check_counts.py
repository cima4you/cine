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

# First, check for episode count patterns
for item in data:
    t = item['title']
    m = re.search(r'(\d+)\s*حلقة', t)
    if m:
        print(f'{m.group(1):>4s} حلقة | {t[:50]}')

print('---')

# Then check what the highest episode number is per series
groups = {}
for item in data:
    series = extract_series_name(item['title'])
    ep_m = re.search(r'الحلقة\s*(\d+)', item['title'])
    ep_num = int(ep_m.group(1)) if ep_m else 0
    if series not in groups:
        groups[series] = {'items': [], 'max_ep': 0}
    groups[series]['items'].append(item)
    if ep_num > groups[series]['max_ep']:
        groups[series]['max_ep'] = ep_num

for series, info in sorted(groups.items(), key=lambda x: -x[1]['max_ep']):
    max_ep = info['max_ep']
    count = len(info['items'])
    if max_ep > 0:
        print(str(max_ep).rjust(4) + ' حلقات | ' + series[:40] + ' (' + str(count) + ' مدخل)')
