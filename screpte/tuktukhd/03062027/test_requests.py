import requests, re

headers = {'User-Agent': 'Mozilla/5.0'}
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

url = 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%AA%D8%B1%D9%83%D9%8A'
print('Fetching {}...'.format(url))
r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
print('Status:', r.status_code)
text = r.content.decode('utf-8')
print('Length:', len(text))
hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
print('Hrefs:', len(hrefs))
alts = re.findall(r'alt="([^"]+)"', text)
print('Alts:', len(alts))

for alt, href in zip(alts[:len(hrefs)], hrefs):
    alt = alt.strip()
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
    if m:
        print('  MATCH:', m.group(1).strip(), m.group(2))
    else:
        print('  NO MATCH:', alt[:50])
