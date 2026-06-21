import json, re, requests, base64, concurrent.futures, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

anime = [(i, x) for i, x in enumerate(d) if x.get('type') in ('أنمي', 'انمي') 
         and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2023]

def has_multi_quality(item):
    servers = item.get('servers', [])
    for s in servers if isinstance(servers, list) else []:
        name = s.get('name', '')
        if 'متعدد' in name or 'جودة' in name:
            return True
    return False

def has_servers(item):
    servers = item.get('servers', [])
    return bool(servers) if isinstance(servers, list) else False

multi = [(i, x) for i, x in anime if has_multi_quality(x)]
no_servers = [(i, x) for i, x in anime if not has_servers(x)]

print('=== Multi-quality (2) ===')
for idx, item in multi:
    print('  Index {}: "{}" ({})'.format(idx, item.get('title','').strip()[:60], item.get('year','')))
    print('    Servers: {}'.format([s.get('name','') for s in item.get('servers',[])]))
    if 'poster' in item:
        print('    Poster: {}...'.format(item['poster'][:70]))
    print()

print('=== No servers (6) ===')
for idx, item in no_servers:
    print('  Index {}: "{}" ({})'.format(idx, item.get('title','').strip()[:60], item.get('year','')))
    # Check if they have tuktukhd poster
    has_tuk = 'tuktukhd' in item.get('poster', '')
    print('    Has tuktukhd poster: {}'.format(has_tuk))
    print()
