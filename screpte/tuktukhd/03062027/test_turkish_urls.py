import requests, re
# Try exact category URL from browser
urls_to_try = [
    'https://tuktukhd.com/category/%D8%AA%D8%B1%D9%83%D9%8A/',
    'https://tuktukhd.com/category/%D8%AA%D8%B1%D9%83%D9%8A/page/1/',
    'https://tuktukhd.com/category/%D8%AA%D8%B1%D9%83%D9%8A/page/2/',
    'https://tuktukhd.com/category/movies-2/%D8%AA%D8%B1%D9%83%D9%8A/',
    'https://tuktukhd.com/category/movies-2/%D8%AA%D8%B1%D9%83%D9%8A/page/1/',
    'https://tuktukhd.com/category/movies-2/%D8%AA%D8%B1%D9%83%D9%8A/page/2/',
]
for url in urls_to_try:
    r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=15, allow_redirects=True)
    hrefs = re.findall(r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+', r.text)
    print(f'{url} -> status={r.status_code}, hrefs={len(hrefs)}, final={r.url}')
