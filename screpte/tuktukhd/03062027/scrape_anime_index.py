import requests, re, html, concurrent.futures, json

headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a'

def scrape_listing(url):
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            return []
        items = re.findall(
            r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="(\u0641\u064A\u0644\u0645[^"]+)"[^>]*>.*?</a>',
            r.text, re.DOTALL
        )
        results = []
        for href, alt in items:
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', alt)
            if m:
                name = m.group(1).strip()
                year = m.group(2)
                name = html.unescape(name)
                results.append({'name': name, 'year': year, 'url': href})
        return results
    except:
        return []

# Quickly find last page by scanning in chunks
import math
max_pages = 500
last_page = max_pages

# Test pages in logarithmic steps
test_pages = list(range(50, 200, 50)) + list(range(200, max_pages + 1, 100))
for p in test_pages:
    url = '{}page/{}/'.format(CATEGORY, p)
    entries = scrape_listing(url)
    print('Page {}: {} entries'.format(p, len(entries)))
    if not entries:
        last_page = p
        break

print('Last page detected: ~{}'.format(last_page))

# Build all page URLs
page_urls = []
for page in range(1, last_page):
    url = '{}page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY
    page_urls.append(url)

all_index = []
p = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
    futures = [ex.submit(scrape_listing, url) for url in page_urls]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        entries = future.result()
        all_index.extend(entries)
        p += 1
        if p % 10 == 0:
            print('  {}/{} pages done, total entries: {}'.format(p, len(page_urls), len(all_index)))

# Deduplicate by URL
seen_urls = set()
deduped = []
for m in all_index:
    if m['url'] not in seen_urls:
        seen_urls.add(m['url'])
        deduped.append(m)

print('Total entries: {} (after dedup: {})'.format(len(all_index), len(deduped)))

out_file = 'scripts/tuktukhd/data/tuktuk_anime_index.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)
print('Saved index to {}'.format(out_file))
