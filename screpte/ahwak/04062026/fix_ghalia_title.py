import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])
prefix = c[:c.index('[')]
suffix = c[c.rindex(']')+1:]

# Find "غالية" with year 2024
for i, item in enumerate(data):
    title = item.get('title', '')
    year = item.get('year', '')
    if 'غالية' in title and year == '2024':
        print('Found: Item %d: "%s" (%s)' % (i, title, year))
        print('  Old poster:', item.get('poster','')[:60])
        item['title'] = 'بـ١٠٠ راجل'
        item['poster'] = 'https://media0101.elcinema.com/uploads/_315x420_73bea89c4d7d257e8d672d94a821ee126cf82b151769b18e561c62747b6594b5.jpg'
        print('  Changed to: "%s"' % item['title'])
        print('  New poster:', item['poster'][:60])
        break

json_str = json.dumps(data, ensure_ascii=False)
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('data.js updated')
