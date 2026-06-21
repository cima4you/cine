import json

with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
d = json.loads(c[c.index('['):c.rindex(']')+1])

asian2026 = [x for x in d if x.get('type') == 'أسيوي' and x.get('year') == '2026']
print('Asian 2026 movies: {}'.format(len(asian2026)))
print()
for x in asian2026:
    rate = x.get('rate', '0')
    imdb = x.get('imdb', '-')
    print('rate={:>4}  imdb={}  "{}"'.format(rate, imdb, x.get('title','').strip()))
