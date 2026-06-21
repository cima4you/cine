import json, re

with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
d = json.loads(c[c.index('['):c.rindex(']')+1])

asian = [x for x in d if x.get('type') == 'أسيوي']
print('Total Asian movies: {}'.format(len(asian)))

with_rate = sum(1 for x in asian if x.get('rate'))
without_rate = sum(1 for x in asian if not x.get('rate'))
print('With rating: {}'.format(with_rate))
print('Without rating: {}'.format(without_rate))

# Show a few with ratings
print('\nAsian movies WITH ratings (sample):')
for x in asian:
    if x.get('rate'):
        print('  {} ({}) -> rate: {}'.format(x.get('title','').strip(), x.get('year',''), x.get('rate')))
        break

# Show a few without ratings
print('\nAsian movies WITHOUT ratings (first 15):')
count = 0
for x in asian:
    if not x.get('rate'):
        print('  "{}" ({})'.format(x.get('title','').strip(), x.get('year','')))
        count += 1
        if count >= 15:
            break

# Check if any have IMDB IDs
with_imdb = sum(1 for x in asian if x.get('imdb'))
print('\nWith IMDB ID: {}'.format(with_imdb))
