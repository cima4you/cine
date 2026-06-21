import requests, sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Accept': 'application/json'})

# Test Wikipedia API for finding IMDB IDs
title = 'La casa de papel'
r = s.get('https://en.wikipedia.org/w/api.php', params={
    'action': 'query',
    'format': 'json',
    'titles': title,
    'prop': 'extracts|pageprops',
    'ppprop': 'wikibase_item',
    'explaintext': True,
    'exintro': True
})
print(f'Wikipedia: {r.status_code}')
data = r.json()
print(json.dumps(data, indent=2, ensure_ascii=False)[:500])

# Try search
r2 = requests.get('https://en.wikipedia.org/w/api.php', params={
    'action': 'query',
    'format': 'json',
    'list': 'search',
    'srsearch': title,
    'srlimit': 3
})
print(f'\nSearch results:')
for p in r2.json().get('query', {}).get('search', []):
    print(f'  {p["title"]}')
