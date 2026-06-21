import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'all_items_reference.txt')

lines = []
for i, item in enumerate(data):
    title = item.get('title', '')
    year = item.get('year', '')
    poster = item.get('poster', '')
    ctype = item.get('contentType', 'movie')
    lines.append('%d | %s | %s | %s | %s' % (i, title, year, ctype, poster))

with open(outpath, 'w', encoding='utf-8') as f:
    f.write('ID | Title | Year | Type | Poster\n')
    f.write('-' * 120 + '\n')
    f.write('\n'.join(lines))

print('Saved %d items to %s' % (len(lines), outpath))
