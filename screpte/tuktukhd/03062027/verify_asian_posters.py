import json, re

with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
d = json.loads(c[c.index('['):c.rindex(']')+1])

asian = [x for x in d if x.get('type') == 'أسيوي']

# Show poster source distribution
tuktuk = sum(1 for x in asian if 'tuktukhd' in x.get('poster', ''))
egydead = sum(1 for x in asian if 'egydead' in x.get('poster', ''))
other = sum(1 for x in asian if x.get('poster') and 'tuktukhd' not in x.get('poster','') and 'egydead' not in x.get('poster',''))
none_ = sum(1 for x in asian if not x.get('poster'))
print('Poster sources for {} Asian movies:'.format(len(asian)))
print('  tuktukhd.com: {}'.format(tuktuk))
print('  egydead.fyi: {}'.format(egydead))
print('  other: {}'.format(other))
print('  none: {}'.format(none_))

# Show sample new posters
print('\nSample updated posters (tuktukhd):')
count = 0
for x in asian:
    if 'tuktukhd' in x.get('poster','') and len(x.get('poster','')) > 10:
        print('  {} ({})'.format(x.get('title','').strip(), x.get('year','')))
        print('    {}'.format(x['poster'][:80]))
        count += 1
        if count >= 5:
            break

# Show movies that couldn't be matched
print('\nMovies NOT matched to tuktukhd (still have non-tuktukhd posters):')
count = 0
for x in asian:
    if x.get('poster') and 'tuktukhd' not in x.get('poster','') and 'egydead' in x.get('poster',''):
        print('  {} ({})'.format(x.get('title','').strip(), x.get('year','')))
        count += 1
        if count >= 10:
            break
if count == 0:
    print('  (none)')
