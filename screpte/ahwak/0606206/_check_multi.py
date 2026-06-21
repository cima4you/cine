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

# Show multi-season series
multi = [(item['title'], len(item.get('seasons', []))) for item in items if len(item.get('seasons', [])) > 1]
multi.sort(key=lambda x: -x[1])
print(f"Multi-season series: {len(multi)}")
for title, count in multi[:15]:
    print(f"  {title[:35]}: {count} مواسم")
