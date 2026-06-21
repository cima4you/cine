import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.5'
})

# Check if there's a movie page with image data
r = s.get('https://www.themoviedb.org/movie/27205', allow_redirects=True)
print(f'TMDB movie page: {r.status_code} {len(r.text)}')

# Find open graph image
for m in re.finditer(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', r.text):
    print(f'og:image: {m.group(1)[:120]}')

# Find all image URLs  
for m in re.finditer(r'(?:https?:)?//image\.tmdb\.org/t/p/[^"\'\\> ]+', r.text):
    print(f'TMDB img: {m.group()[:120]}')

# Look for JSON-LD
for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', r.text, re.DOTALL):
    import json
    try:
        ld = json.loads(m.group(1))
        if 'image' in ld:
            print(f'JSON-LD image: {ld["image"][:120]}')
    except:
        print(f'JSON-LD found but not parsed')
