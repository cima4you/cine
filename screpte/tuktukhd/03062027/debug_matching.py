import requests, re, json
headers = {'User-Agent': 'Mozilla/5.0'}
BASE = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a'

r = requests.get(BASE, timeout=15, headers=headers, allow_redirects=True)
alts = re.findall(r'alt="([^"]+)"', r.text)
print('=== TUKTUKHD listing titles (first 15) ===')
for a in alts[:15]:
    # Parse alt
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', a)
    if m:
        eng = m.group(1).strip()
        year = m.group(2)
        print('  alt="{}" -> name="{}" year={}'.format(a, eng, year))

# Now load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

# Show some data.js foreign item titles
print('\n=== DATA.JS foreign item titles (first 15) ===')
for item in data_js:
    if item.get('type') == 'أجنبي':
        title = item.get('title', '').strip()
        year = item.get('year', '')
        print('  title="{}" year={}'.format(title, year))

# And multi-quality ones
print('\n=== DATA.JS multi-quality items (first 15) ===')
target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']
count = 0
for item in data_js:
    servers = item.get('servers', [])
    if any(s.get('name', '') in target_servers for s in servers):
        title = item.get('title', '').strip()
        year = item.get('year', '')
        print('  title="{}" year={} type={}'.format(title, year, item.get('type','')))
        count += 1
        if count >= 15:
            break
