import json, re

with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
d = json.loads(c[c.index('['):c.rindex(']')+1])

asian = [x for x in d if x.get('type') == 'أسيوي']
with_rate = sum(1 for x in asian if x.get('rate') and float(x.get('rate', 0)) > 0)
no_rate = sum(1 for x in asian if not x.get('rate') or float(x.get('rate', 0)) == 0)
with_imdb = sum(1 for x in asian if x.get('imdb'))

print('Asian movies: {}'.format(len(asian)))
print('With rating: {}'.format(with_rate))
print('Without rating: {}'.format(no_rate))
print('With IMDB ID: {}'.format(with_imdb))

if no_rate > 0:
    print('\nStill unrated:')
    for x in asian:
        if not x.get('rate') or float(x.get('rate', 0)) == 0:
            print('  "{}" ({})'.format(x.get('title','').strip(), x.get('year','')))

# Show sample
print('\nSample ratings:')
for x in asian:
    if x.get('rate') and float(x.get('rate', 0)) > 0:
        print('  "{}" ({}) -> {}'.format(x.get('title','').strip(), x.get('year',''), round(float(x['rate']), 1)))
        break
