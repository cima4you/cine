import json, re
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data = json.loads(content[start:end])

# Check what fields foreign items have
foreign_items = [item for item in data if item.get('type') == 'اجنبي']
print('Foreign items: {}'.format(len(foreign_items)))

# Check what types exist
types = set()
for item in data:
    types.add(item.get('type', ''))
print('All types: {}'.format(sorted(types)))

# Check "أجنبي" vs "اجنبي" encoding
print('\nType values hex:', [t.encode('utf-8').hex() for t in sorted(types)])

# Find the actual foreign type
for t in sorted(types):
    items = [item for item in data if item.get('type') == t]
    print('\nType "{}" ({} items)'.format(t, len(items)))
    # Show first 3 titles
    for i, item in enumerate(items[:3]):
        title = item.get('title', '')
        year = item.get('year', '')
        print('  [{}] title="{}" year={}'.format(i, title, year))
    # Check for items with multi-quality servers
    multi_count = 0
    for item in items:
        for s in item.get('servers', []):
            if s.get('name', '') in ['متعدد الجودة', 'سيرفر متعدد', 'سيرفر رئيسي', 'سيرفر متعدد الجودات', 'سرفر متعدد', 'سرفر متعدد الجودات']:
                multi_count += 1
                break
    if multi_count:
        print('  -> Multi-quality servers: {}'.format(multi_count))

# Check what keys exist
all_keys = set()
for item in data:
    all_keys.update(item.keys())
print('\nAll keys in data: {}'.format(sorted(all_keys)))

# Check for imdb_id, tmdb_id
has_imdb = sum(1 for item in data if item.get('imdb_id'))
has_tmdb = sum(1 for item in data if item.get('tmdb_id'))
print('Items with imdb_id: {}'.format(has_imdb))
print('Items with tmdb_id: {}'.format(has_tmdb))
