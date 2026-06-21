import requests, re, json

base = 'https://www.ooanime.com'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

results = {}

# Check main categories
cats = ['/tvseries', '/anime', '/cartoon', '/movie', '/series']
for cat in cats:
    r = requests.get(base + cat, headers=headers, timeout=10)
    r.encoding = 'utf-8'
    unique_series = len(set(re.findall(r'/series/(\d+)/', r.text)))
    series_links = len(re.findall(r'/series/(\d+)/', r.text))
    results[cat] = f'unique: {unique_series}, total links: {series_links}, size: {len(r.text)}'

# Check if there are category pages with query params
for q in ['كرتون', 'انمي', 'انيميشن', 'مغامرة', 'اكشن']:
    r = requests.get(base + f'/tvseries?category={q}&search=', headers=headers, timeout=10)
    r.encoding = 'utf-8'
    unique = len(set(re.findall(r'/series/(\d+)/', r.text)))
    results[f'/tvseries?category={q}'] = f'unique: {unique}'

# Check the homepage for total counts
r = requests.get(base, headers=headers, timeout=10)
r.encoding = 'utf-8'
# Count series mentioned anywhere
all_series = set(re.findall(r'/series/(\d+)/', r.text))
results['homepage_unique_series'] = len(all_series)

# Look at the footer info
counts = re.findall(r'عدد\s*المسلسلات[^<]*<[^>]*>(\d+)', r.text)
results['series_count_footer'] = counts

# Check for total episode count
ep_counts = re.findall(r'عدد\s*الحلقات[^<]*<[^>]*>(\d+)', r.text)
results['episode_count_footer'] = ep_counts

# Check other nav links
nav_links = re.findall(r'href="/([^"]+)"', r.text)
nav_sections = [l for l in nav_links if not any(x in l for x in ['http','www','#','javascript'])]
results['nav_sections'] = list(set(nav_sections))[:20]

print(json.dumps(results, ensure_ascii=False, indent=2))
