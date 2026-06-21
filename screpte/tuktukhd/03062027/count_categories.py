import requests, re, sys, json, concurrent.futures, base64
from urllib.parse import unquote

headers = {'User-Agent': 'Mozilla/5.0'}
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

categories = {
    'اجنبي': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D8%AC%D9%86%D8%A8%D9%8A',
    'هندي': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%87%D9%86%D8%AF%D9%89',
    'اسيوي': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D8%B3%D9%8A%D9%88%D9%8A',
    'تركي': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%AA%D8%B1%D9%83%D9%8A',
    'مدبلجة': 'https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%85%D8%AF%D8%A8%D9%84%D8%AC%D8%A9',
    'نتفليكس': 'https://tuktukhd.com/channel/film-netflix-1',
    'انمي': 'https://tuktukhd.com/category/anime-6/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D9%86%D9%85%D9%8A',
}

# First determine page counts for each category
def count_pages(cat_url):
    total = 0
    for page in range(1, 300):
        url = '{}page/{}/'.format(cat_url, page) if page > 1 else cat_url
        try:
            r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
            text = r.content.decode('utf-8')
            hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
            alts = re.findall(r'alt="([^"]+)"', text)
            entries = 0
            for alt, href in zip(alts[:len(hrefs)], hrefs):
                alt = alt.strip()
                if re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt):
                    entries += 1
            if not entries:
                return total, page
            total += entries
        except:
            return total, page
    return total, 300

print('Counting pages per category...')
cat_info = {}
for cat_key, cat_url in categories.items():
    total, last_page = count_pages(cat_url)
    cat_info[cat_key] = {'total': total, 'pages': last_page - 1}
    print('  {}: {} movies, {} pages'.format(cat_key, total, last_page - 1))
