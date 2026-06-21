import json, re

with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
d = json.loads(c[c.index('['):c.rindex(']')+1])

anime = [x for x in d if x.get('type') in ('أنمي', 'انمي')]
print('Total anime in data.js: {}'.format(len(anime)))

# from 2024 and older
anime_old = [x for x in anime if str(x.get('year', '')).isdigit() and int(x.get('year', 0)) <= 2024]
print('Anime from 2024 and older: {}'.format(len(anime_old)))

# Poster sources
tuktuk = sum(1 for x in anime_old if 'tuktukhd' in x.get('poster', ''))
egydead = sum(1 for x in anime_old if 'egydead' in x.get('poster', ''))
other = sum(1 for x in anime_old if x.get('poster') and 'tuktukhd' not in x.get('poster','') and 'egydead' not in x.get('poster',''))
none_ = sum(1 for x in anime_old if not x.get('poster'))
print('Poster sources:')
print('  tuktukhd: {}'.format(tuktuk))
print('  egydead: {}'.format(egydead))
print('  other: {}'.format(other))
print('  none: {}'.format(none_))

# Sample posters
print('\nSample posters (first 5 2024 anime):')
count = 0
for x in anime_old:
    if x.get('year') == '2024':
        print('  "{}" ({}) -> {}'.format(x.get('title','').strip()[:40], x.get('year',''), x.get('poster','(none)')[:70]))
        count += 1
        if count >= 5:
            break
