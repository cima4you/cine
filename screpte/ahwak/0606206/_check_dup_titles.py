import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

def norm(t):
    return re.sub(r'[\u064B-\u0652]', '', re.sub(r'\s+', '', (t or '').strip().lower()))

# Parse merged completed file
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

# Find duplicate titles
seen = {}
dup_titles = []
for item in items:
    key = norm(item.get('title', ''))
    if key in seen:
        dup_titles.append((item.get('title', '')[:40], seen[key].get('title', '')[:40]))
    else:
        seen[key] = item

print(f"Total series: {len(items)}")
print(f"Duplicate titles: {len(dup_titles)}")
for t1, t2 in dup_titles[:10]:
    print(f"  {t1} == {t2}")
