import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
})

# Try TMDB website search - look for movie IDs and poster images
r = s.get('https://www.themoviedb.org/search?query=Inception&language=en-US', allow_redirects=True)
print(f'TMDB search: {r.status_code} {len(r.text)}')
if r.status_code == 200 and len(r.text) > 1000:
    # Find poster images
    for m in re.finditer(r'https://image\.tmdb\.org/t/p/[^"\'\\]+', r.text):
        print(f'  TMDB img: {m.group()[:120]}')
    # Find movie links
    for m in re.finditer(r'href="/movie/(\d+)[^"]*"[^>]*>([^<]+)</a>', r.text):
        print(f'  Movie: {m.group(1)} - {m.group(2).strip()[:80]}')
else:
    print(f'  Response first 1000 chars: {r.text[:1000]}')
    # Look for any image URLs or movie data
    # Find all unique image-like URLs
    for m in re.finditer(r'https?://[^"\'\\> ]+\.(?:jpg|png|jpeg|webp)', r.text):
        url = m.group()
        if 'tmdb' in url.lower() or 'image' in url.lower():
            print(f'  IMG: {url[:120]}')
    # Find poster_path in any JSON
    for m in re.finditer(r'poster_path["\']?\s*[:=]\s*["\']([^"\']+)["\']', r.text):
        print(f'  poster_path: {m.group(1)[:80]}')
    # Find movie/tv IDs
    for m in re.finditer(r'(?:/movie/|/tv/)(\d+)[^"\']*["\']', r.text):
        print(f'  ID: {m.group(1)}')
    # Check if there's JSON-LD
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', r.text, re.DOTALL):
        print(f'  JSON-LD found: {m.group(1)[:200]}')
