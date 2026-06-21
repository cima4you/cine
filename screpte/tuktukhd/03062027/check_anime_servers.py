import json, re, requests, base64, concurrent.futures, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

anime = [(i, x) for i, x in enumerate(d) if x.get('type') in ('أنمي', 'انمي') 
         and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2023]

print('Anime 2023- in data.js: {}'.format(len(anime)))

# Check server status
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
good = [(i, x) for i, x in anime if has_servers(x) and not has_multi_quality(x)]

print('Multi-quality servers: {}'.format(len(multi)))
print('No servers: {}'.format(len(no_servers)))
print('Already good: {}'.format(len(good)))

# Show sample multi-quality
if multi:
    print('\nSample multi-quality:')
    for idx, item in multi[:5]:
        servers = item.get('servers', [])
        names = [s.get('name','') for s in servers]
        print('  "{}" ({}) -> servers: {}'.format(item.get('title','').strip()[:50], item.get('year',''), names))
