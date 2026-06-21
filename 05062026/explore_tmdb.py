import requests, json, sys, time
sys.stdout.reconfigure(encoding='utf-8')

TMDB_KEY = "0301bf9dd3a630dcbbea37f5c2b07d3e"
headers = {"Accept": "application/json"}

def tmdb_get(url, params):
    params["api_key"] = TMDB_KEY
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 429:
                print("  [ratelimited, waiting 5s]")
                time.sleep(5)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  [error: {e}]")
            if attempt == 2:
                return None
            time.sleep(2)
    return None

# Test 1: Discover Arabic TV series from 2025
print('=== Discover Arabic TV series 2025 ===')
url = "https://api.themoviedb.org/3/discover/tv"
params = {
    "first_air_date_year": 2025,
    "with_original_language": "ar",
    "sort_by": "popularity.desc",
    "page": 1,
}
data = tmdb_get(url, params)
if data:
    total_pages = data.get("total_pages", 0)
    total_results = data.get("total_results", 0)
    print(f'Total results: {total_results}, pages: {total_pages}')
    for r in data.get("results", [])[:10]:
        poster = f"https://image.tmdb.org/t/p/w500{r['poster_path']}" if r.get('poster_path') else "N/A"
        print(f'  {r.get("name")} ({r.get("first_air_date", "N/A")}) - rate: {r.get("vote_average", 0)} - poster: {poster[:80]}')

# Test 2: Also try with original_language not specified to get more
print('\n=== Discover all TV series 2025 with Arabic keyword ===')
params2 = {
    "first_air_date_year": 2025,
    "sort_by": "popularity.desc",
    "page": 1,
    "with_keywords": "arabic|arab",
}
data2 = tmdb_get(url, params2)
if data2:
    print(f'Total results: {data2.get("total_results", 0)}, pages: {data2.get("total_pages", 0)}')

# Test 3: Get all pages for Arabic series 2025
print('\n=== Test pagination for Arabic 2025 ===')
all_series = []
for page in range(1, min(4, total_pages + 1) if data else 1):
    p = {"first_air_date_year": 2025, "with_original_language": "ar", "sort_by": "popularity.desc", "page": page}
    d = tmdb_get(url, p)
    if d and d.get("results"):
        all_series.extend(d["results"])
    time.sleep(0.3)

print(f'Total collected: {len(all_series)}')
for s in all_series[:5]:
    print(f'  {s.get("name")} - {s.get("first_air_date", "N/A")}')

# Test 4: Check a specific work page on elcinema
print('\n=== Test elcinema search for a specific title ===')
es = requests.Session()
es.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
})
es.get('https://www.elcinema.com/', timeout=15)

for title in ['المداح', 'جعفر العمدة']:
    r = es.get('https://www.elcinema.com/search/', params={'q': title}, timeout=15)
    if r.status_code == 200:
        links = re.findall(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)', r.text)
        if links:
            name = links[0][1].strip()
            href = links[0][0]
            # Get work page for poster
            r2 = es.get(f'https://www.elcinema.com{href}', timeout=15)
            poster = re.search(r'<img[^>]*src="([^"]*_315x420[^"]*)"', r2.text)
            poster_url = poster.group(1) if poster else "N/A"
            print(f'  {title}: elcinema="{name}", poster={poster_url[:80]}')
        else:
            print(f'  {title}: no results')
    else:
        print(f'  {title}: HTTP {r.status_code}')
