import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

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

# Find a series with duplicate seasons and show full structure
for item in items:
    seasons = item.get('seasons', [])
    if len(seasons) > 1:
        print(f"Title: {item['title'][:40]}")
        for i, s in enumerate(seasons):
            print(f"  Season {i}: keys={list(s.keys())}")
            print(f"    season={s.get('season')}, seasonNumber={s.get('seasonNumber')}")
            print(f"    episodes count={len(s.get('episodes', []))}")
            if s.get('episodes'):
                ep = s['episodes'][0]
                print(f"    Sample ep keys={list(ep.keys())}")
        break
