import requests, re, json

# Check actual categories of a few Turkish page entries
headers = {'User-Agent': 'Mozilla/5.0'}

with open('scripts/tuktukhd/data/turkish_listing.json', 'r', encoding='utf-8') as f:
    movies = json.load(f)

# Check categories of first 20 movies
for m in movies[:20]:
    r = requests.get(m['url'], headers=headers, timeout=15)
    # Find catssection
    cats = re.findall(r'<a[^>]*href="[^"]*category[^"]*"[^>]*>([^<]+)</a>', r.text)
    real_cats = [c.strip() for c in cats if c.strip() not in ('الرئيسية', 'الأفلام', 'جميع الافلام', 'الحلقات', 'جميع الحلقات', 'مسلسلات')]
    print(f'  "{m["name"][:40]}" ({m["year"]}) -> cats: {real_cats[:5]}')
