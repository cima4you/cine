import json

GENRE_MAP = {
    'Action': 'أكشن', 'Adventure': 'مغامرة', 'Animation': 'رسوم متحركة',
    'Biography': 'سيرة ذاتية', 'Comedy': 'كوميديا', 'Crime': 'جريمة',
    'Documentary': 'وثائقي', 'Drama': 'دراما', 'Family': 'عائلي',
    'Fantasy': 'فنتازيا', 'History': 'تاريخي', 'Horror': 'رعب',
    'Musical': 'موسيقي', 'Mystery': 'غموض', 'Romance': 'رومانسي',
    'Sci-Fi': 'خيال علمي', 'Sport': 'رياضي', 'Thriller': 'إثارة',
    'War': 'حرب', 'Western': 'ويسترن', 'Film-Noir': 'فيلم نوار',
    'Music': 'موسيقى', 'News': 'أخبار', 'Reality-TV': 'تلفزيون واقعي',
    'Talk-Show': 'برنامج حواري', 'Game-Show': 'برنامج مسابقات',
    'Short': 'فيلم قصير', 'Adult': 'للكبار فقط',
}

def translate_genre(genre_str):
    genres = [g.strip() for g in genre_str.split(',')]
    result = []
    for g in genres:
        result.append(GENRE_MAP.get(g, g))
    return result

with open('screpte/imdb/data/top250.json', 'r', encoding='utf-8') as f:
    movies = json.load(f)

entries = []
for m in movies:
    poster = m.get('poster', '') or ''
    desc = m.get('plot', '') or ''
    year = m.get('year', '') or ''
    rating = m.get('imdb_rating', '') or ''
    genre_str = m.get('genre', '') or ''
    categories = translate_genre(genre_str)
    imdb_id = m['imdb_id']
    server_url = f'https://streamimdb.ru/embed/movie/{imdb_id}'

    entry = {
        'title': m['title'],
        'year': year,
        'rating': rating,
        'type': 'IMDb',
        'contentType': 'movie',
        'description': desc,
        'poster': poster,
        'categories': categories,
        'servers': [
            {'name': 'StreamIMDb', 'url': server_url, 'isDefault': True}
        ],
        'trial': f'https://www.imdb.com/title/{imdb_id}/',
    }
    entries.append(entry)

output = '// IMDb Top 250 — 246 فيلم\n'
output += 'const cd_imdb = '
output += json.dumps(entries, ensure_ascii=False, indent=2)
output += ';\n'

with open('data-imdb.js', 'w', encoding='utf-8') as f:
    f.write(output)

print(f'Saved {len(entries)} entries to data/data-imdb.js')
