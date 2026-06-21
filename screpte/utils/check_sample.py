import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

# Show a few foreign movies
shown = 0
for x in data:
    if x.get('type') == 'أجنبي' and 'imdb' in x.get('poster', '').lower():
        print(f'type={x.get("type")}, contentType={x.get("contentType")}')
        print(f'title={x["title"]}')
        print(f'poster={x["poster"][:100]}')
        print(f'cast={x.get("cast", [])[:3]}')
        print(f'categories={x.get("categories", [])[:3]}')
        print()
        shown += 1
        if shown >= 3:
            break
