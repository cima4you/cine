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
for item in items:
    if 'حفرة' in item.get('title', ''):
        print(item["title"] + ":")
        for s in item.get('seasons', []):
            sn = s.get('seasonNumber', s.get('season', '?'))
            print("  Season " + str(sn) + ": " + str(len(s.get('episodes', []))) + " eps")
        break
