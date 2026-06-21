import requests, sys
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

r = session.get('https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-%D8%A7%D9%84%D8%BA%D8%A7%D8%B6%D8%A8%D9%88%D9%86-2026-%D9%85%D8%AF%D8%A8%D9%84%D8%AC-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/')
soup = BeautifulSoup(r.text, 'html.parser')

poster_block = soup.select_one('div.Poster--Block')
if poster_block:
    with open('poster_check.txt', 'w', encoding='utf-8') as f:
        f.write('Poster Block HTML:\n')
        f.write(str(poster_block)[:1000])
        imgs = poster_block.select('img')
        for img in imgs:
            f.write(f'\n  src: {img.get("src")}\n')
            f.write(f'  data-src: {img.get("data-src")}\n')
else:
    with open('poster_check.txt', 'w', encoding='utf-8') as f:
        f.write('No Poster--Block found\n')
        for sel in ['.Poster--Block img', 'div[class*="Poster"] img', '.poster img']:
            el = soup.select_one(sel)
            if el:
                src = el.get('src')
                ds = el.get('data-src')
                f.write(f'{sel}: src={src}, data-src={ds}\n')
