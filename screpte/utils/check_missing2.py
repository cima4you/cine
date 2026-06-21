import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

missing = [x for x in data if x.get('type') == 'أجنبي' and 'tmdb' not in x.get('poster', '').lower() and 'm.media-amazon' not in x.get('poster', '').lower()]
print(f'Final missing (no poster found): {len(missing)}')
for x in missing:
    print(f'  {x["title"]}')
