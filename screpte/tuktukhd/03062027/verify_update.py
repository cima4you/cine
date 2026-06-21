import json, re

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

# Check: how many items still have multi-quality servers?
remaining = 0
for item in data:
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        remaining += 1

print('Items still with multi-quality servers: {}'.format(remaining))

# Check how many have TukTuk servers
tuktuk_count = 0
for item in data:
    if any('TukTuk' in s.get('name', '') for s in item.get('servers', [])):
        tuktuk_count += 1

print('Items with TukTuk servers: {}'.format(tuktuk_count))

# Check total items
print('Total items: {}'.format(len(data)))

# Check type distribution of remaining multi-quality items
if remaining > 0:
    by_type = {}
    for item in data:
        if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
            t = item.get('type', '')
            by_type[t] = by_type.get(t, 0) + 1
    print('\nRemaining mult-quality by type:')
    for t, c in sorted(by_type.items()):
        print('  {}: {}'.format(t, c))

# Sample a few updated items
print('\nSample updated TukTuk servers:')
count = 0
for item in data:
    for s in item.get('servers', []):
        if 'TukTuk' in s.get('name', ''):
            print('  "{}" ({}) - server: "{}" url: {}'.format(
                item.get('title',''), item.get('year',''), 
                s.get('name',''), s.get('url','')[:50]))
            count += 1
            if count >= 5:
                break
    if count >= 5:
        break
