import re

with open('scripts/tuktukhd/anime_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

alts = re.findall(r'alt="([^"]+)"', html)
hrefs = re.findall(r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+', html, re.IGNORECASE)

print('Alts (all):')
for i, a in enumerate(alts):
    film = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', a)
    print('  {}: {} {}'.format(i, '[FILM]' if film else '[OTHER]', a[:70]))

print('\nHrefs:')
for i, h in enumerate(hrefs):
    print('  {}: {}'.format(i, h[:70]))
