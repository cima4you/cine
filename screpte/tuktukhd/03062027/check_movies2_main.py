import requests, re

headers = {'User-Agent': 'Mozilla/5.0'}
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

# Check the main movies-2 page
url = 'https://tuktukhd.com/category/movies-2/'
print('=== Main movies-2 page ===')
r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
text = r.content.decode('utf-8')

hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
alts = re.findall(r'alt="([^"]+)"', text)
print('Hrefs:', len(hrefs), 'Alts:', len(alts))

matches = []
for alt, href in zip(alts[:len(hrefs)], hrefs):
    alt = alt.strip()
    if alt == 'توك توك سينما':
        continue
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
    if m:
        matches.append((m.group(1).strip(), m.group(2), href))
        
print('Total matches:', len(matches))
for name, year, href in matches[:5]:
    print('  {} ({}) - {}'.format(name[:40], year, href[:60]))

# Also check page 2
print('\n=== movies-2 page 2 ===')
r2 = requests.get(url + 'page/2/', timeout=15, headers=headers, allow_redirects=True)
text2 = r2.content.decode('utf-8')
hrefs2 = re.findall(FILM_PATTERN, text2, re.IGNORECASE)
alts2 = re.findall(r'alt="([^"]+)"', text2)
matches2 = []
for alt, href in zip(alts2[:len(hrefs2)], hrefs2):
    alt = alt.strip()
    if alt == 'توك توك سينما':
        continue
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
    if m:
        matches2.append((m.group(1).strip(), m.group(2), href))
print('Page 2 matches:', len(matches2))
for name, year, href in matches2[:5]:
    print('  {} ({}) - {}'.format(name[:40], year, href[:60]))
