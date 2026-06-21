import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')
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

# Show الحفرة season details
for item in items:
    if 'حفرة' in item.get('title', ''):
        print("Title:", item["title"])
        print("Seasons:", len(item.get("seasons", [])))
        for i, s in enumerate(item.get("seasons", [])):
            eps = s.get("episodes", [])
            print(f"\nSeason {i}: keys={list(s.keys())}")
            print(f"  season={s.get('season')}, seasonNumber={s.get('seasonNumber')}")
            print(f"  episodes={len(eps)}")
            if eps:
                # Show first 3 episode titles
                for j, ep in enumerate(eps[:3]):
                    title = ep.get('title', '')[:50]
                    sv = len(ep.get('servers', []))
                    print(f"    Ep {j}: title='{title}', servers={sv}")
                if len(eps) > 3:
                    print(f"    ... ({len(eps)-3} more)")
                if eps[-1]:
                    title = eps[-1].get('title', '')[:50]
                    sv = len(eps[-1].get('servers', []))
                    print(f"    Last: title='{title}', servers={sv}")
        break
