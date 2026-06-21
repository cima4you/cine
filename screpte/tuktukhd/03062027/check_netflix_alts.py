import requests, re
r = requests.get('https://tuktukhd.com/channel/film-netflix-1/', headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
alts = re.findall(r'alt="([^"]+)"', r.text)
hrefs = re.findall(r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+', r.text)
print('Alt texts:')
for a in alts[:10]:
    print(f'  "{a}"')
print('\nHrefs:', len(hrefs))
for h in hrefs[:5]:
    print(f'  {h[:60]}')
# Try pattern on each alt
for a in alts[:10]:
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', a.strip())
    if m:
        print(f'  MATCH: name="{m.group(1)}", year={m.group(2)}')
    else:
        print(f'  NO MATCH: "{a[:60]}"')
