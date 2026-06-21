import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

# Check elcinema posters in data.js
total = len(data)
elcinema = sum(1 for x in data if 'elcinema' in x.get('poster', '').lower())
larozza_poster = sum(1 for x in data if 'larozza.living' in x.get('poster', '').lower())
other = total - elcinema - larozza_poster

print(f'data.js: {total} items')
print(f'  elcinema.com posters: {elcinema}')
print(f'  larozza.living posters: {larozza_poster}')
print(f'  other posters: {other}')

# Show sample
for x in data:
    if 'elcinema' in x.get('poster', '').lower():
        print(f'  {x["title"]}: {x["poster"][:80]}')
        break
