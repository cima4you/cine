import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.5'
})

r = s.get('https://www.themoviedb.org/search?query=Inception&language=en-US', allow_redirects=True)
print(f'Status: {r.status_code} Length: {len(r.text)}')

# Save HTML for analysis
with open('C:\\Users\\DT01\\AppData\\Local\\Temp\\opencode\\tmdb_search.html', 'w', encoding='utf-8') as f:
    f.write(r.text)

# Search for patterns that might contain movie info
patterns = [
    r'<a[^>]*href="([^"]*/movie/[^"]*)"[^>]*>',
    r'<a[^>]*href="([^"]*)"[^>]*>[^<]*Inception',
    r'data-id=["\'](\d+)["\']',
    r'data-movie',
    r'card[^"]*',
]

for pat_name, pat in [('movie links', r'/movie/\d+'), ('all links', r'href="/(?:movie|tv)/\d+')]:
    matches = re.findall(pat, r.text)
    print(f'{pat_name}: {len(matches)}')
    for m in matches[:10]:
        print(f'  {m}')
