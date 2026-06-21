import json

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

remaining = 0
for item in data:
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        remaining += 1

tuktuk = sum(1 for item in data if any('TukTuk' in s.get('name', '') for s in item.get('servers', [])))

print('=== Final State ===')
print('Total items: {}'.format(len(data)))
print('Items with multi-quality servers: {}'.format(remaining))
print('Items with TukTuk servers: {}'.format(tuktuk))
print()
print('Updated (multi-quality → TukTuk): {}'.format(161))  # 154 + 7
print('Not found (still multi-quality): {}'.format(remaining))
print()
print('Foreign (اجنبي) multi-quality remaining:')
for item in data:
    if item.get('type') == 'أجنبي':
        if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
            print('  "{}" ({})'.format(item.get('title',''), item.get('year','')))

print()
print('File size: {} KB'.format(len(content) / 1024))
