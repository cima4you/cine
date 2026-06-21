import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')

DATA_JS = r'D:\Users\DT01\Desktop\rachid-site\data.js'
LOD_JSON = r'D:\Users\DT01\Desktop\rachid-site\scripts\lodynet\lodynet_formatted.json'

print('Reading data.js...')
with open(DATA_JS, 'r', encoding='utf-8') as f:
    content = f.read()

# Find array bounds
m = re.search(r'(const\s+contentData\s*=\s*)', content)
start_idx = m.end()
depth = 0
for i in range(start_idx, len(content)):
    if content[i] == '[': depth += 1
    elif content[i] == ']':
        depth -= 1
        if depth == 0:
            end_idx = i + 1
            break

prefix = content[:m.start(1)]
decl = content[m.start(1):start_idx]
arr_str = content[start_idx:end_idx]
suffix = content[end_idx:].lstrip(';')

print('Parsing existing array...')
existing = json.loads(arr_str)
print(f'Existing items: {len(existing)}')

print('Reading lodynet data...')
with open(LOD_JSON, 'r', encoding='utf-8') as f:
    lodynet = json.load(f)
print(f'LodyNet items: {len(lodynet)}')

existing_titles = {item.get('title') for item in existing}
new_items = []
dupes = 0
for item in lodynet:
    t = item.get('title')
    if t and t not in existing_titles:
        new_items.append(item)
        existing_titles.add(t)
    else:
        dupes += 1

print(f'New: {len(new_items)}, Dupes: {dupes}')

merged = existing + new_items
print(f'Total: {len(merged)}')

print('Writing data.js...')
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(prefix)
    f.write(decl)
    json.dump(merged, f, ensure_ascii=False, separators=(',', ':'))
    f.write(';' + suffix)

print('Done!')
