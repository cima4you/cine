import json, re
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])
turkish = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي']

print('Turkish movies without rating:')
for idx, item in turkish:
    rating = item.get('rating', 0)
    if not rating or float(rating) == 0:
        print('  NO RATING: idx={} "{}" ({}) imdb={}'.format(
            idx, item.get('title','').strip()[:50], item.get('year',''), item.get('imdbID','')))

print('\nTurkish movies with suspicious rating (title seems wrong):')
for idx, item in turkish:
    title = item.get('title','').strip()
    if re.match(r'^\d{4}$', title) or title == '' or title == ' ':
        print('  BAD TITLE: idx={} "{}" ({}) rating={}'.format(
            idx, title[:30], item.get('year',''), item.get('rating',0)))
