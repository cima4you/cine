import re

with open('scripts/tuktukhd/anime_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

alts = re.findall(r'alt="([^"]+)"', html)
film_alts = [a for a in alts if re.match(r'فيلم\s+.+?\s+\d{4}\s+مترجم', a)]
print('Total alt texts:', len(alts))
print('Matching film alt texts:', len(film_alts))

hrefs = re.findall(r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+', html, re.IGNORECASE)
print('Film URLs:', len(hrefs))

# Find articles
articles = re.findall(r'<article[^>]*>.*?</article>', html, re.DOTALL)
print('Articles found:', len(articles))

for i, art in enumerate(articles[:3]):
    img = re.search(r'<img[^>]+alt="([^"]+)"', art)
    link = re.search(r'href="([^"]+)"', art)
    if img and link:
        print('  Article {}: alt={} url={}'.format(i+1, img.group(1)[:60], link.group(1)[:60]))
