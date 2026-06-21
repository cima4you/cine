import requests, re
for p in [1, 5, 10, 20]:
    url = 'https://tuktukhd.com/channel/film-netflix-1/page/{}/'.format(p) if p > 1 else 'https://tuktukhd.com/channel/film-netflix-1/'
    r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
    hrefs = re.findall(r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+', r.text)
    alts = re.findall(r'alt="([^"]+)"', r.text)
    print('Page {}: hrefs={}, alts={}, status={}'.format(p, len(hrefs), len(alts), r.status_code))
