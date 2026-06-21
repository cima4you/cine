import requests, re, json

url = 'https://tuktukhd.com/series/%D9%85%D8%B3%D9%84%D8%B3%D9%84-from-%D9%85%D8%AA%D8%B1%D8%AC%D9%85/'
html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text

# Check the allseasonss section
ss = re.search(r'<section class="allseasonss">(.*?)</section>', html, re.DOTALL)
if ss:
    content = ss.group(1)
    season_blocks = re.findall(r'<a\s+href="(https://tuktukhd\.com/series/[^"]+)"[^>]*>.*?<h3>(.*?)</h3>', content, re.DOTALL)
    result = {'blocks_found': len(season_blocks), 'blocks': []}
    for surl, sname in season_blocks:
        sn = re.sub(r'<[^>]+>', '', sname).strip()
        sn_m = re.search(r'(\d+)', sn)
        sn_num = int(sn_m.group(1)) if sn_m else 0
        result['blocks'].append({'seasonNumber': sn_num, 'name': sn, 'url': surl})
    print('Season blocks:', json.dumps(result, ensure_ascii=False, indent=2))
else:
    print('NO allseasonss section found')
    # Try partial match
    pos = html.find('allseasons')
    if pos >= 0:
        print('Found "allseasons" at position', pos)
        print('Context:', html[pos-50:pos+100])
    else:
        print('"allseasons" not found in HTML')
