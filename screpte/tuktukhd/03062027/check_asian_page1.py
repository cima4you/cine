import requests, re

CATEGORY = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%b3%d9%8a%d9%88%d9%8a'
r = requests.get(CATEGORY, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
alts = re.findall(r'alt="([^"]+)"', r.text)
hrefs = re.findall(r'href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"', r.text, re.IGNORECASE)

print('First 20 Asian movies on page 1:')
for alt, href in zip(alts[:20], hrefs[:20]):
    alt = alt.strip()
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', alt)
    if m:
        eng = m.group(1).strip()
        year = m.group(2)
        # Extract slug from URL
        slug = href.split('/')[-2] if href.endswith('/') else href.split('/')[-1]
        print('  "{}" ({}) -> slug: {}'.format(eng, year, slug[:60]))
