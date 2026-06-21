import json, re
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data = json.loads(content[start:end])

target_names = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات', 'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']
items_with_multi = []
for item in data:
    servers = item.get('servers', [])
    matching_servers = [s for s in servers if s.get('name', '') in target_names]
    if matching_servers:
        items_with_multi.append({
            'name': item.get('name', ''),
            'year': item.get('year', ''),
            'type': item.get('type', ''),
            'servers': matching_servers,
            'total_servers': len(servers),
            'downloads': bool(item.get('downloadServers'))
        })

print('Total items with multi-quality servers: {}'.format(len(items_with_multi)))
for m in items_with_multi:
    names = [s['name'] for s in m['servers']]
    print('  {} ({}) [{}] - {} - download: {} - total: {}'.format(
        m['name'], m['year'], m['type'], names, m['downloads'], m['total_servers']))
