import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Parse completed file
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

# Find series with old format servers (name: "watch")
old_format = []
new_format = []
no_episodes = []

for item in items:
    has_seasons = False
    for s in item.get('seasons', []):
        for ep in s.get('episodes', []):
            has_seasons = True
            sv = ep.get('servers', [])
            if sv:
                # Check format
                if isinstance(sv, list) and sv:
                    sname = sv[0].get('name', '')
                    if sname == 'watch' or sname == 'WATCH':
                        old_format.append(item.get('title', '')[:50])
                        break
                    elif sname and sname not in ('watch', 'WATCH'):
                        new_format.append(item.get('title', '')[:50])
                        break
            break
        break
    if not has_seasons:
        no_episodes.append(item.get('title', '')[:50])

print(f"Total series: {len(items)}")
print(f"Old format (name=watch): {len(old_format)}")
print(f"New format (real names): {len(new_format)}")

if old_format:
    print("\nOld format series (first 20):")
    for name in old_format[:20]:
        print(f"  {name}")

if new_format:
    print(f"\nNew format series (first 10):")
    for name in new_format[:10]:
        print(f"  {name}")

if no_episodes:
    print(f"\nNo episodes: {no_episodes}")
