import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Parse merged completed file in detail
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

# Find ALL duplicate seasons (by season value)
dups_found = 0
for item in items:
    seasons = item.get('seasons', [])
    counts = {}
    for s in seasons:
        sn = s.get('season')
        # Also check seasonNumber
        if sn is None:
            sn = s.get('seasonNumber')
        # Convert to string for counting
        skey = str(sn) if sn is not None else 'null'
        counts[skey] = counts.get(skey, 0) + 1
    
    for skey, count in counts.items():
        if count > 1:
            dups_found += 1
            if dups_found <= 20:
                # Print the actual season values
                actual_seasons = [s.get('season') for s in seasons if str(s.get('season') if s.get('season') is not None else 'null') == skey]
                ep_counts = [len(s.get('episodes', [])) for s in seasons if str(s.get('season') if s.get('season') is not None else 'null') == skey]
                print(f"{dups_found}. {item['title'][:40]}: Season key={skey} appears {count}x, eps={ep_counts}")

print(f"\nTotal duplicate season groups: {dups_found}")
