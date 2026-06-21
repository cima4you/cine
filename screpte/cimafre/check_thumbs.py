import json, re

m = json.load(open('data/data-cimafre.json','r',encoding='utf-8'))
for i in range(min(5, len(m))):
    t = m[i].get('thumb','') or m[i].get('thumb_url','') or 'NONE'
    print(f'[{i}] {t[:100]}')

with open('data/data-cimafre.js','r',encoding='utf-8') as f:
    content = f.read()
matches = re.findall(r'thumb:"([^"]*)"', content)
print(f'First 3 JS thumbs: {matches[:3]}')
print()

# check what createCard uses
# In the modal it uses item.poster - do cimafre items have a poster field?
print(f'Has poster field: {"poster" in m[0]}')
print(f'Keys: {list(m[0].keys())}')
