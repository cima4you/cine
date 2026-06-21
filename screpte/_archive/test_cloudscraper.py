import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper()
r = scraper.get('https://www.imdb.com/title/tt1375666/', timeout=15)
print('Status:', r.status_code)
print('Length:', len(r.text))

if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'html.parser')
    rating_el = soup.select_one('div[data-testid="hero-rating-bar__aggregate-rating__score"] span')
    if rating_el:
        print('Rating:', rating_el.text.strip())
    else:
        ratings = re.findall(r'"ratingValue":\s*([\d.]+)', r.text)
        if ratings:
            print('Rating from JSON-LD:', ratings[0])
        else:
            print('No rating found in page')
else:
    print('Body:', r.text[:500])
