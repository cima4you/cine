import json

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

remaining = []
for item in data:
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        remaining.append(item)

tuktuk = sum(1 for item in data if any('TukTuk' in s.get('name', '') for s in item.get('servers', [])))

print('Total items: {}'.format(len(data)))
print('Items with TukTuk servers: {}'.format(tuktuk))
print('Items still with multi-quality: {}'.format(len(remaining)))

if remaining:
    by_type = {}
    for item in remaining:
        t = item.get('type', '')
        by_type[t] = by_type.get(t, 0) + 1
    print('\nRemaining by type:')
    for t, c in sorted(by_type.items()):
        print('  {}: {}'.format(t, c))
    print('\nRemaining items:')
    for item in remaining:
        print('  "{}" ({}) [{}]'.format(
            item.get('title','').strip(), item.get('year',''), item.get('type','')))
else:
    print('\nAll multi-quality servers replaced!')

print('\nFile size: {:.0f} KB'.format(len(content) / 1024))
