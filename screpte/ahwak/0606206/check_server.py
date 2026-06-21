import json
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_full.json', encoding='utf-8') as f:
    d = json.load(f)

# Find series with no servers or partially missing
no_servers = []
partial = []
for item in d:
    has = 0
    total = 0
    for s in item.get('seasons', []):
        for ep in s.get('episodes', []):
            total += 1
            if ep.get('servers'):
                has += 1
    if has == 0 and total > 0:
        no_servers.append((item['title'], total))
    elif has < total:
        partial.append((item['title'], has, total))

print(f'=== Series with ZERO servers ({len(no_servers)}) ===')
for t, c in sorted(no_servers, key=lambda x: -x[1]):
    print(f'  {t}: {c} eps')

print(f'\n=== Partial servers ({len(partial)}) ===')
for t, h, c in sorted(partial, key=lambda x: -(x[2]-x[1])):
    print(f'  {t}: {h}/{c} have servers')
