import requests, re, sys
from urllib.parse import unquote

headers = {'User-Agent': 'Mozilla/5.0'}

categories = {
    'اجنبي': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D8%AC%D9%86%D8%A8%D9%8A',
    'هندي': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%87%D9%86%D8%AF%D9%89',
    'اسيوي': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D8%B3%D9%8A%D9%88%D9%8A',
    'تركي': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%AA%D8%B1%D9%83%D9%8A',
    'مدبلجة': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%85%D8%AF%D8%A8%D9%84%D8%AC%D8%A9',
    'نتفليكس': 'https://tuktukhd.com/channel/film-netflix-1',
    'انمي': 'https://tuktukhd.com/category/anime-6/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D9%86%D9%85%D9%8A',
}

FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

def scrape_listing(cat_url, max_pages=200):
    results = []
    for page in range(1, max_pages + 1):
        url = '{}page/{}/'.format(cat_url, page) if page > 1 else cat_url
        try:
            r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
            text = r.content.decode('utf-8')
            alts = re.findall(r'alt="([^"]+)"', text)
            hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
            entries = 0
            for alt, href in zip(alts[:len(hrefs)], hrefs):
                alt = alt.strip()
                m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
                if m:
                    results.append({'name': m.group(1).strip(), 'year': m.group(2), 'url': href})
                    entries += 1
            if not entries:
                break
            print('  {} - page {}: {} (total: {})'.format(unquote(cat_url).split('/')[-1], page, entries, len(results)))
        except:
            break
    return results

all_listed = {}
for cat_key, cat_url in categories.items():
    print('\nScraping {}...'.format(cat_key))
    results = scrape_listing(cat_url)
    all_listed[cat_key] = results
    print('  Total for {}: {}'.format(cat_key, len(results)))

# Summary
print('\n\n=== SUMMARY ===')
total = 0
for cat, items in all_listed.items():
    print('{}: {}'.format(cat, len(items)))
    total += len(items)
print('Total: {}'.format(total))

# Check overlap
all_urls = {}
for cat, items in all_listed.items():
    for item in items:
        url = item['url']
        if url not in all_urls:
            all_urls[url] = []
        all_urls[url].append(cat)

# Count URLs appearing in multiple categories
multi = {url: cats for url, cats in all_urls.items() if len(cats) > 1}
print('\nURLs in multiple categories: {}'.format(len(multi)))
if multi:
    print('Sample:')
    for url, cats in list(multi.items())[:5]:
        print('  {} -> {}'.format(url[:50], cats))
