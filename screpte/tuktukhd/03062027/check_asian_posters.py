import json, re

with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

asian_2024 = [x for x in data if x.get('type') == 'أسيوي' and x.get('year') == '2024']
print('Asian 2024 movies: {}'.format(len(asian_2024)))

no_poster = []
for item in asian_2024:
    poster = item.get('poster', '')
    title = item.get('title', '').strip()
    if not poster:
        no_poster.append(title)
        print('  NO POSTER: "{}"'.format(title))
    elif len(poster) < 10:
        no_poster.append(title)
        print('  BAD POSTER: "{}" -> {}'.format(title, poster))

print('\nMissing posters: {}'.format(len(no_poster)))
