import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

missing = [x for x in data if x.get('type') == 'أجنبي' and 'tmdb' not in x.get('poster', '').lower()]
print(f'Missing TMDB posters: {len(missing)}')
print('\n--- Samples ---')
for x in missing[:20]:
    print(f'  {x["title"]} | poster={x["poster"][:60]} | year={x.get("year","")}')
print(f'\n--- Total: {len(missing)} missing ---')
