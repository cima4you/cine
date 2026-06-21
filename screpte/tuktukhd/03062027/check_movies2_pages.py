import requests, re
headers = {'User-Agent': 'Mozilla/5.0'}
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

# Check movies-2/افلام-تركي page 1 vs category/تركي page 1
urls = [
    ('movies-2/افلام-تركي', 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%AA%D8%B1%D9%83%D9%8A'),
    ('category/تركي', 'https://tuktukhd.com/category/%D8%AA%D8%B1%D9%83%D9%8A'),
]

for label, url in urls:
    r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
    text = r.content.decode('utf-8')
    hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
    alts = re.findall(r'alt="([^"]+)"', text)
    entries = []
    for alt, href in zip(alts[:len(hrefs)], hrefs):
        alt = alt.strip()
        m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
        if m:
            entries.append((m.group(1), m.group(2)))
    print('{}: {} entries'.format(label, len(entries)))
    for name, year in entries[:3]:
        print('  {} ({})'.format(name[:40], year))
    print()

# Also check movies-2/افلام-اجنبي
for cat in ['اجنبي', 'هندي', 'اسيوي', 'مدبلجة']:
    encoded = '%D8%A7%D9%81%D9%84%D8%A7%D9%85-' + {
        'اجنبي': '%D8%A7%D8%AC%D9%86%D8%A8%D9%8A',
        'هندي': '%D9%87%D9%86%D8%AF%D9%89',
        'اسيوي': '%D8%A7%D8%B3%D9%8A%D9%88%D9%8A',
        'مدبلجة': '%D9%85%D8%AF%D8%A8%D9%84%D8%AC%D8%A9',
    }[cat]
    url = 'https://tuktukhd.com/category/movies-2/' + encoded
    r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
    text = r.content.decode('utf-8')
    hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
    alts = re.findall(r'alt="([^"]+)"', text)
    entries = []
    for alt, href in zip(alts[:len(hrefs)], hrefs):
        alt = alt.strip()
        m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
        if m:
            entries.append((m.group(1), m.group(2)))
    print('movies-2/{}: {} entries'.format(cat, len(entries)))
    for name, year in entries[:3]:
        print('  {} ({})'.format(name[:40], year))
    print()
