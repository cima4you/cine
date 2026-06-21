import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8')

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
})

# Try IMDB search
r = s.get('https://www.imdb.com/find/?q=Inception&s=tt', allow_redirects=True)
print(f'IMDB find: {r.status_code} {len(r.text)}')
if r.status_code == 200 and len(r.text) > 1000:
    # Look for poster images
    for m in re.finditer(r'https://m\.media-amazon\.com/images/[^"\'\\]+', r.text):
        print(f'  IMG: {m.group()[:120]}')
    # Look for title results
    for m in re.finditer(r'<a[^>]*href="/title/tt(\d+)/"[^>]*>([^<]+)</a>', r.text):
        print(f'  Result: tt{m.group(1)} - {m.group(2).strip()[:80]}')
else:
    print(f'  Response: {r.text[:300]}')

# Try TMDB as alternative
r2 = s.get('https://api.themoviedb.org/3/search/movie?api_key=1f7d8a7e9c5e5c5c5c5c5c5c5c5c5c5c&query=Inception')
print(f'\nTMDB: {r2.status_code}')
if r2.status_code == 200:
    data = r2.json()
    if data['results']:
        m = data['results'][0]
        print(f'  Title: {m["title"]}')
        print(f'  Poster: https://image.tmdb.org/t/p/w500{m["poster_path"]}')
