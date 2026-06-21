import json

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Check last 150 entries
print('Last 150 entries:')
for idx, item in enumerate(d[-150:], len(d)-150):
    t = item.get('type', '')
    title = item.get('title', '').strip()[:30]
    year = item.get('year', '')
    poster = 'tuk' if 'tuktukhd' in item.get('poster','') else 'other'
    print(f'  {idx}: type={t}, title="{title}", year={year}, poster={poster}')
