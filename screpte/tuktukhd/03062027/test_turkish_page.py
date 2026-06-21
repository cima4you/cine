import requests, re
CATEGORY = 'https://tuktukhd.com/category/%D8%AA%D8%B1%D9%83%D9%8A'
# Try with and without trailing slash
for page in [1, 2]:
    for suffix in ['/', '']:
        if page > 1:
            url = '{}{}page/{}/'.format(CATEGORY, suffix, page)
        else:
            url = '{}{}'.format(CATEGORY, suffix)
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
        hrefs = re.findall(r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+', r.text)
        print(f'Page {page}, suffix="{suffix}/": hrefs={len(hrefs)}, status={r.status_code}')
        if hrefs:
            print(f'  First: {hrefs[0][:60]}')
