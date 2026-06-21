import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check source data for "الحفرة" season numbers
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_full.json', 'r', encoding='utf-8') as f:
    source = json.load(f)

# Also check old formatted data
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\ahwaktv_data_formatted.json', 'r', encoding='utf-8') as f:
    old = json.load(f)

# Find الحفرة in both
def norm(t):
    import re
    return re.sub(r'[\u064B-\u0652]', '', re.sub(r'\s+', '', (t or '').strip().lower()))

for item in source:
    if 'حفرة' in item.get('title', ''):
        print(f"Source: {item['title']}")
        for s in item.get('seasons', []):
            print(f"  Season: {s.get('season')}, eps: {len(s.get('episodes', []))}")
        break

for item in old:
    if 'حفرة' in item.get('title', ''):
        print(f"Old: {item['title']}")
        for s in item.get('seasons', []):
            print(f"  Season: {s.get('season')}, eps: {len(s.get('episodes', []))}")
        break

# Also check the merged completed file
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-completed.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'\[\s*\{', content, re.DOTALL)
start = m.start()
depth = 0
for i in range(start, len(content)):
    if content[i] == '[': depth += 1
    elif content[i] == ']':
        depth -= 1
        if depth == 0:
            items = json.loads(content[start:i+1])
            break

for item in items:
    if 'حفرة' in item.get('title', ''):
        print(f"Merged: {item['title']}")
        for s in item.get('seasons', []):
            print(f"  Season: {s.get('season')}, eps: {len(s.get('episodes', []))}")
