from tmdbv3api import TMDb, Movie
import json
import requests
import time

# Try common TMDb API keys or ask user to provide
# For now, let's try the Wikipedia approach first
def find_imdb_via_wikipedia(title, year):
    """Search Wikipedia for a movie and try to find its IMDB ID"""
    headers = {'User-Agent': 'RachidMovies/1.0 (movie-site)'}
    
    search_query = f'{title} {year} film'
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': search_query,
        'format': 'json',
        'srlimit': 5
    }
    try:
        r = requests.get('https://en.wikipedia.org/w/api.php', params=params, headers=headers, timeout=10)
        data = r.json()
        pages = data.get('query', {}).get('search', [])
        
        for p in pages:
            page_title = p['title']
            # Get page props which often contain IMDB ID
            params2 = {
                'action': 'query',
                'titles': page_title,
                'prop': 'pageprops',
                'format': 'json'
            }
            r2 = requests.get('https://en.wikipedia.org/w/api.php', params=params2, headers=headers, timeout=10)
            data2 = r2.json()
            pages2 = data2.get('query', {}).get('pages', {})
            for pid, info in pages2.items():
                props = info.get('pageprops', {})
                imdb_id = props.get('imdb_id', '')
                if imdb_id:
                    return imdb_id
        return None
    except Exception as e:
        print(f'  Wiki error: {e}')
        return None

# Test
test_titles = [
    ('Vadh 2', '2026'),
    ('Raja Shivaji', '2026'),
    ('Sampradayaini Suppini Suddapusaani', '2026'),
]

for title, year in test_titles:
    print(f'{title} ({year})...')
    imdb_id = find_imdb_via_wikipedia(title, year)
    if imdb_id:
        print(f'  Found: {imdb_id}')
    else:
        print(f'  Not found on Wikipedia')
    print()
