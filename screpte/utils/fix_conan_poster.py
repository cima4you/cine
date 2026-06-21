import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])
prefix = c[:c.index('[')]
suffix = c[c.rindex(']')+1:]

poster_url = 'https://m.arabseed.show/wp-content/uploads/2023/12/MV5BNDhhM2IwYWMtN2ExYy00ZDhhLTg2MmQtZjhmNmQxMWM3ZTg3XkEyXkFqcGdeQXVyNzEyMDQ1MDA@.jpg_V1_SX700-388x550.webp'

for i, item in enumerate(data):
    title = item.get('title', '')
    if 'كونان' in title and 'غواصة' in title:
        print('Found: [%d] %s' % (i, title))
        print('  Old poster: %s' % item.get('poster','')[:60])
        item['poster'] = poster_url
        print('  New poster set')
        break
else:
    print('Not found in data.js')
    # Try partial search
    for i, item in enumerate(data):
        title = item.get('title', '')
        if 'كونان' in title and '2023' in item.get('year',''):
            print('  Partial: [%d] %s (%s)' % (i, title, item.get('year','')))

json_str = json.dumps(data, ensure_ascii=False)
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('data.js saved')
