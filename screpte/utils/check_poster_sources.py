import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

# Check poster sources for foreign movies
sources = {}
for x in data:
    if x.get('type') == 'أجنبي':
        p = x.get('poster', '')
        domain = re.search(r'https?://([^/]+)', p)
        if domain:
            d = domain.group(1)
            sources[d] = sources.get(d, 0) + 1

print('Poster sources for foreign movies:')
for d, n in sorted(sources.items(), key=lambda x: -x[1])[:20]:
    print(f'  {d}: {n}')

# Check if any have imdb in poster
imdb_posters = sum(1 for x in data if x.get('type') == 'أجنبي' and 'imdb' in x.get('poster', '').lower())
media_amazon = sum(1 for x in data if x.get('type') == 'أجنبي' and 'media-amazon' in x.get('poster', ''))
print(f'\nIMDB posters: {imdb_posters}')
print(f'media-amazon posters: {media_amazon}')
