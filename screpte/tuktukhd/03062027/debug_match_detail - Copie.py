import json, re

with open('scripts/tuktukhd/data/tuktuk_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

# Get all multi-quality items with their normalized titles
multi_items = []
for item in data_js:
    servers = item.get('servers', [])
    if any(s.get('name', '') in target_servers for s in servers):
        title = item.get('title', '').strip()
        year = str(item.get('year', ''))
        ptype = item.get('type', '')
        multi_items.append({
            'title': title,
            'year': year,
            'type': ptype,
            'norm': re.sub(r'\s+\d{4}$', '', title.lower().strip())
        })

def norm_title(t):
    return re.sub(r'\s+\d{4}$', '', t.lower().strip())

# Try matching with each multi item
print('Attempting detailed matching...')
found_any = False
for m in multi_items:
    nt = m['norm']
    y = m['year']
    # Exact match
    for item in index:
        if item['title'].lower() == nt and item['year'] == y:
            print('MATCH FOUND: "{}" ({}) <-> "{}" ({})'.format(
                m['title'], y, item['title'], item['year']))
            found_any = True
            break
    if not found_any:
        # Try substring match
        for item in index:
            if y == item['year'] and (nt in item['title'].lower() or item['title'].lower() in nt):
                print('CLOSE: "{}" ({}) <-> "{}" ({})'.format(
                    m['title'], y, item['title'], item['year']))
                found_any = True
                break

if not found_any:
    print('No matches at all!')
    # Debug: show a few keys from both
    print('\nIndex keys sample (first 20):')
    for i, item in enumerate(index[:20]):
        print('  "{}" ({})'.format(item['title'], item['year']))
    print('\nMulti-quality keys sample (first 20):')
    for m in multi_items[:20]:
        print('  "{}" ({}) [norm="{}"]'.format(m['title'], m['year'], m['norm']))
