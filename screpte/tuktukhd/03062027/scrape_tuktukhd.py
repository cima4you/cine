import requests, re, json, concurrent.futures, urllib.parse, sys
from difflib import SequenceMatcher

headers = {'User-Agent': 'Mozilla/5.0'}
BASE = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a'

def scrape_listing_page(page):
    url = '{}page/{}/'.format(BASE, page) if page > 1 else BASE
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            return []
        # Extract movie blocks
        alt_matches = re.findall(r'alt="([^"]+)"', r.text)
        href_matches = re.findall(r'href="(https://tuktukhd\.com/%d9%81%d9%8a%d9%84%d9%85[^"]+)"', r.text)
        
        results = []
        for alt, href in zip(alt_matches, href_matches):
            # Parse alt: "فيلم ENGLISH_NAME YEAR مترجم اون لاين"
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', alt)
            if m:
                eng_name = m.group(1).strip()
                year = m.group(2)
                results.append({
                    'title': eng_name,
                    'year': year,
                    'alt': alt,
                    'url': href
                })
        return results
    except Exception as e:
        return []

# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

# Extract foreign movie names from data.js for matching
foreign_items = [item for item in data_js if item.get('type') == 'اجنبي']
print('Foreign movies in data.js: {}'.format(len(foreign_items)))

# Scrape first 50 pages
all_listed = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    results = list(ex.map(scrape_listing_page, range(1, 51)))

for page_movies in results:
    all_listed.extend(page_movies)

print('Scraped {} movie listings from 50 pages'.format(len(all_listed)))

# Save index
with open('scripts/tuktukhd/data/tuktuk_index.json', 'w', encoding='utf-8') as f:
    json.dump(all_listed, f, ensure_ascii=False, indent=2)

# Build lookup by year then by normalized English name
def normalize(name):
    return re.sub(r'[^a-z0-9]', '', name.lower().strip())

index_by_year = {}
for m in all_listed:
    year = m['year']
    norm = normalize(m['title'])
    if year not in index_by_year:
        index_by_year[year] = {}
    index_by_year[year][norm] = m

# Match with data.js foreign items
matched = []
unmatched = []
multi_quality = []

for item in foreign_items:
    name = item.get('name', '')
    year = str(item.get('year', ''))
    
    # Check if item has a multi-quality server
    servers = item.get('servers', [])
    has_multi = any(s.get('name', '') in [
        'متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
        'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي'
    ] for s in servers)
    
    # Try to extract English name from Arabic name
    # data.js stores names as Arabic (translated titles)
    # Try matching by finding the year in the index
    year_index = index_by_year.get(year, {})
    
    best_match = None
    best_score = 0.5
    
    for norm_url, movie_data in year_index.items():
        # Compare with the name (both sides normalized)
        # The name in data.js is Arabic, but the tuktukhd title is English
        # We can't directly match them...
        pass
    
    # Since we can't match Arabic → English easily, let's just store the info
    info = {
        'data_name': name,
        'data_year': year,
        'has_multi_quality': has_multi,
        'server_count': len(servers),
        'downloads': bool(item.get('downloadServers'))
    }
    
    if has_multi:
        info['servers'] = servers
        multi_quality.append(info)
    else:
        unmatched.append(info)

print('\nMulti-quality items: {}'.format(len(multi_quality)))
print('Other items: {}'.format(len(unmatched)))
print('\nTotal foreign items: {}'.format(len(foreign_items)))

# Also show what years are available in the index
years_available = sorted(index_by_year.keys(), reverse=True)
print('\nYears available in index (first 20): {}'.format(years_available[:20]))
print('Total unique years: {}'.format(len(years_available)))
