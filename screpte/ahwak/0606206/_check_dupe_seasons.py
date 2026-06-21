import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check completed file for duplicate seasons
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

# Find duplicate season numbers
dups = []
for item in items:
    seasons = item.get('seasons', [])
    seen = {}
    for s in seasons:
        sn = s.get('season', 0)
        if sn in seen:
            dups.append((item.get('title', '')[:30], sn, seen[sn], s.get('episodes', [])[:1]))
        seen[sn] = s

print(f"Series with duplicate seasons: {len(dups)}")
for title, sn, first_s, first_ep in dups[:10]:
    print(f"  {title}: Season {sn} appears twice")
    # Check episodes in each
    print(f"    First has {len(first_s.get('episodes',[]))} eps, second has {len(first_s.get('episodes',[]))} eps")
