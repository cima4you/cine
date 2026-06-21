import json, sys

with open('scripts/new_asian_results.json', 'r', encoding='utf-8') as f:
    new_items = json.load(f)

print('Movies ready to add: {}'.format(len(new_items)))
for i, item in enumerate(new_items):
    print('  {}. "{}" ({}) [{} servers]'.format(i + 1, item['title'], item['year'], len(item.get('servers', []))))

print('\nOptions:')
print('  1. Add ALL to data.js')
print('  2. Add specific numbers (e.g. 1,3,5-10)')
print('  3. Cancel')

choice = input('\nChoice: ').strip()

if choice == '1':
    selected = new_items
elif choice == '2':
    nums = input('Enter numbers (e.g. 1,3,5-10): ').strip()
    indices = set()
    for part in nums.split(','):
        part = part.strip()
        if '-' in part:
            a, b = part.split('-')
            for n in range(int(a.strip()), int(b.strip()) + 1):
                indices.add(n - 1)
        else:
            indices.add(int(part) - 1)
    selected = [new_items[i] for i in sorted(indices) if 0 <= i < len(new_items)]
elif choice == '3':
    print('Cancelled')
    sys.exit(0)
else:
    print('Invalid choice')
    sys.exit(0)

if not selected:
    print('No items selected')
    sys.exit(0)

print('\nAdding {} items to data.js...'.format(len(selected)))

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

import re
existing = set()
for item in data_js:
    existing.add((norm(item.get('title', '')), str(item.get('year', ''))))

added = 0
skipped = 0
for item in selected:
    key = (norm(item['title']), item['year'])
    if key in existing:
        print('  SKIP: "{}" ({}) - already exists'.format(item['title'], item['year']))
        skipped += 1
        continue
    # Add standard fields
    item['trial'] = ''
    item['contentType'] = 'movie'
    data_js.append(item)
    added += 1
    print('  ADD: "{}" ({})'.format(item['title'], item['year']))

if added > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    json_str = json.dumps(data_js, ensure_ascii=False)
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)
    print('\nAdded: {}, Skipped: {}'.format(added, skipped))
    print('data.js now has {} items'.format(len(data_js)))
else:
    print('No new items added')
