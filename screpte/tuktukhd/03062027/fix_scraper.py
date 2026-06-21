import requests, re, json, concurrent.futures, base64, sys

headers = {'User-Agent': 'Mozilla/5.0'}
BASE = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a'
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

def scrape_listing_page(page):
    url = '{}page/{}/'.format(BASE, page) if page > 1 else BASE
    try:
        r = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            return []
        alts = re.findall(r'alt="([^"]+)"', r.text)
        hrefs = re.findall(FILM_PATTERN, r.text, re.IGNORECASE)
        results = []
        for alt, href in zip(alts, hrefs):
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', alt)
            if m:
                eng_name = m.group(1).strip()
                year = m.group(2)
                results.append({
                    'title': eng_name,
                    'year': year,
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

# Extract items needing update
target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

items_to_update = []
for idx, item in enumerate(data_js):
    servers = item.get('servers', [])
    if any(s.get('name', '') in target_servers for s in servers):
        title = item.get('title', '').strip()
        year = str(item.get('year', ''))
        items_to_update.append({
            'data_index': idx,
            'title': title,
            'year': year,
            'item_type': item.get('type', ''),
        })

print('Items needing update: {}'.format(len(items_to_update)))

def norm_title(title):
    title = title.strip()
    title = re.sub(r'\s+\d{4}$', '', title)
    return title.lower().strip()

# Build update lookup
update_lookup = {}
for it in items_to_update:
    t = norm_title(it['title'])
    y = it['year']
    key = (t, y)
    if key not in update_lookup:
        update_lookup[key] = []
    update_lookup[key].append(it)

# Show a few sample keys
print('Sample update keys (first 10):')
for i, k in enumerate(list(update_lookup.keys())[:10]):
    print('  "{}" (year={})'.format(k[0], k[1]))

# Scrape tuktukhd listing pages
print('Scraping tuktukhd pages...')
all_listed = []
page = 1
while page <= 100:
    entries = scrape_listing_page(page)
    if not entries and page > 3:
        break
    all_listed.extend(entries)
    if page == 1 or page % 10 == 0:
        print('  Page {}: {} (total: {})'.format(page, len(entries), len(all_listed)))
    page += 1

print('Total tuktukhd listings: {} from {} pages'.format(len(all_listed), page - 1))

# Save index
try:
    with open('scripts/tuktukhd/data/tuktuk_index.json', 'w', encoding='utf-8') as f:
        json.dump(all_listed, f, ensure_ascii=False, indent=2)
    print('Index saved to scripts/tuktuk_index.json')
except Exception as e:
    print('Error saving index: {}'.format(e))

# Build tuktukhd lookup
tuktuk_index = {}
for m in all_listed:
    t = m['title'].lower().strip()
    y = m['year']
    key = (t, y)
    if key not in tuktuk_index:
        tuktuk_index[key] = []
    tuktuk_index[key].append(m['url'])

print('Tuktuk index has {} unique keys'.format(len(tuktuk_index)))

# Test a specific match
test_key = ('erupcja', '2026')
print('Test lookup "erupcja"/2026: {}'.format(test_key in tuktuk_index))
if test_key in tuktuk_index:
    print('  URL: {}'.format(tuktuk_index[test_key]))

# Match
matched = []
unmatched = []
for key, items in update_lookup.items():
    tuktuk_urls = tuktuk_index.get(key, [])
    if tuktuk_urls:
        for it in items:
            matched.append({
                'data_item': it,
                'tuktuk_url': tuktuk_urls[0]
            })
    else:
        unmatched.extend(items)

print('\nMatched: {}'.format(len(matched)))
print('Unmatched: {}'.format(len(unmatched)))

# Show a few unmatched examples with possible close matches
if unmatched:
    print('\nSample unmatched:')
    sample = unmatched[:5]
    for u in sample:
        norm_t = norm_title(u['title'])
        y = u['year']
        print('  "{}" ({}) -> normalised="{}"'.format(u['title'], y, norm_t))
        # Find close keys in tuktuk
        close = []
        for k in tuktuk_index:
            if k[1] == y and (norm_t in k[0] or k[0] in norm_t):
                close.append(k)
        if close:
            for c in close[:2]:
                print('    Close tuktuk key: "{}"'.format(c))

if matched:
    print('\nSample matched:')
    for m in matched[:5]:
        print('  "{}" ({}) -> {}'.format(m['data_item']['title'], m['data_item']['year'], m['tuktuk_url'][:60]))

# Save match info
with open('scripts/tuktukhd/data/tuktuk_matched.json', 'w', encoding='utf-8') as f:
    json.dump(matched, f, ensure_ascii=False, indent=2)
print('\nMatch data saved')
