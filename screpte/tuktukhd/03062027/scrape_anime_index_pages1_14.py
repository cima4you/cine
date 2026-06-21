import requests, re, json, html

headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a'

def scrape_listing(url):
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            return []
        items = re.findall(
            r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="([^"]+)"[^>]*>.*?</a>',
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

# Scrape ONLY pages 1-14 sequentially (reliable)
all_index = []
for page in range(1, 15):
    url = '{}page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY
    entries = scrape_listing(url)
    print('Page {}: {} entries'.format(page, len(entries)))
    all_index.extend(entries)

# Deduplicate by URL
seen_urls = set()
deduped = []
for m in all_index:
    if m['url'] not in seen_urls:
        seen_urls.add(m['url'])
        deduped.append(m)

print('Total entries: {} (after dedup: {})'.format(len(all_index), len(deduped)))

# Save index
with open('scripts/tuktukhd/data/tuktuk_anime_index_v2.json', 'w', encoding='utf-8') as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)
print('Saved index to scripts/tuktukhd/data/tuktuk_anime_index_v2.json')
