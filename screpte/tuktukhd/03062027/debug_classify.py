import requests, re, base64
headers = {'User-Agent': 'Mozilla/5.0'}
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

url = 'https://tuktukhd.com/category/movies-2/'
r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
text = r.content.decode('utf-8')
hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
alts = re.findall(r'alt="([^"]+)"', text)

TYPE_KEYWORDS = {
    'أجنبي': [],
    'هندي':  ['هندي', 'هندى'],
    'أسيوي': ['أسيوي', 'اسيوي', 'آسيوي'],
    'تركي':  ['تركي', 'تركى', 'تركية'],
    'مدبلج': ['مدبلج', 'مدبلجة', 'مدبلج'],
    'نتفليكس': ['نتفليكس', 'نتفلكس', 'نتفلکس', 'نتفلیکس', 'Netflix', 'نيتفليكس'],
    'أنمي':  ['انمي', 'أنمي', 'انمى', 'أنمى', 'Anime'],
}

def classify_categories(cats):
    for t, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if any(kw in c for c in cats):
                return t
    return 'أجنبي'

count = 0
for alt, href in zip(alts[:len(hrefs)], hrefs):
    alt = alt.strip()
    if alt == 'توك توك سينما':
        continue
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
    if m and count < 5:
        count += 1
        name, year = m.group(1).strip(), m.group(2)
        print('Movie: {} ({})'.format(name[:40], year))
        print('  URL: {}'.format(href[:80]))
        
        # Get detail page
        try:
            r2 = requests.get(href, timeout=15, headers=headers)
            html = r2.content.decode('utf-8')
            
            # Find breadcrumb categories
            cats = []
            seen_cats = set()
            breadcrumb = re.findall(r'<a[^>]*href="[^"]*category[^"]*"[^>]*>([^<]+)</a>', html)
            for c in breadcrumb:
                c = c.strip()
                if c and c not in ('الرئيسية', 'الأفلام', 'جميع الافلام', 'الحلقات', 'جميع الحلقات', 'مسلسلات') and c not in seen_cats:
                    cats.append(c)
                    seen_cats.add(c)
            
            # Also check channel
            if 'film-netflix' in html or 'نتفليكس' in html or 'Netflix' in html:
                cats.append('نتفليكس')
            
            print('  Categories found: {}'.format(cats))
            ptype = classify_categories(cats)
            print('  Classified: {}'.format(ptype))
        except Exception as e:
            print('  Error: {}'.format(e))
