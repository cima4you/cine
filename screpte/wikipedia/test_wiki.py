import requests
# Test: Can we find an IMDB ID via Wikipedia for an Indian movie?

test_titles = [
    'Vadh 2 2026',
    'Raja Shivaji 2026',
    'Mrithyunjay 2026',
]

for title in test_titles:
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': title,
        'format': 'json',
        'srlimit': 3
    }
    r = requests.get('https://en.wikipedia.org/w/api.php', params=params, timeout=10)
    data = r.json()
    pages = data.get('query', {}).get('search', [])
    print(f'{title}: {len(pages)} results')
    for p in pages[:2]:
        print(f'  - {p["title"]}')
    # Get page content for first result to look for IMDB ID
    if pages:
        page_title = pages[0]['title']
        params2 = {
            'action': 'query',
            'titles': page_title,
            'prop': 'extracts|pageprops',
            'exintro': True,
            'explaintext': True,
            'format': 'json'
        }
        r2 = requests.get('https://en.wikipedia.org/w/api.php', params=params2, timeout=10)
        data2 = r2.json()
        pages2 = data2.get('query', {}).get('pages', {})
        for pid, info in pages2.items():
            props = info.get('pageprops', {})
            print(f'  Props: {dict(list(props.items())[:5])}')
            imdb_id = props.get('imdb_id', props.get('imdbid', 'NOT FOUND'))
            print(f'  IMDB ID: {imdb_id}')
    print()
