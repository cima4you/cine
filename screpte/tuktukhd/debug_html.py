import requests, re, json

r = requests.get('https://tuktukhd.com/series/%D9%85%D8%B3%D9%84%D8%B3%D9%84-from-%D9%85%D8%AA%D8%B1%D8%AC%D9%85/', 
    headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

output = {}

# Catssection
cs = re.search(r'<div class="catssection"[^>]*>(.*?)</section>', html, re.DOTALL)
if cs:
    content = cs.group(1)
    genre_li = re.search(r'<span>\u0627\u0644\u0627\u0646\u0648\u0627\u0639</span>(.*?)</li>', content, re.DOTALL)
    if genre_li:
        genres = re.findall(r'<a[^>]*>([^<]+)</a>', genre_li.group(1))
        output['genres'] = genres
    cat_li = re.search(r'<span>\u0627\u0644\u062a\u0635\u0646\u064a\u0641\u0627\u062a</span>(.*?)</li>', content, re.DOTALL)
    if cat_li:
        cats = re.findall(r'<a[^>]*>([^<]+)</a>', cat_li.group(1))
        output['categories'] = cats

# Seasons section
ss = re.search(r'<section class="allseasonsss">(.*?)</section>', html, re.DOTALL)
if ss:
    season_blocks = re.findall(r'<a\s+href="(https://tuktukhd\.com/series/[^"]+)"[^>]*>.*?<h3>(.*?)</h3>', ss.group(1), re.DOTALL)
    output['seasons'] = []
    for surl, sname in season_blocks:
        sn = re.sub(r'<[^>]+>', '', sname).strip()
        sn_m = re.search(r'(\d+)', sn)
        sn_num = int(sn_m.group(1)) if sn_m else 0
        output['seasons'].append({'seasonNumber': sn_num, 'name': sn, 'url': surl})

# Episodes section
es = re.search(r'<section class="[^"]*allepcont[^"]*"[^>]*>(.*?)</section>', html, re.DOTALL)
if es:
    ep_blocks = re.findall(r'<a\s+href="(https://tuktukhd\.com/[^"]*)"[^>]*title="([^"]*)"', es.group(1))
    output['episodes'] = []
    for eurl, etitle in ep_blocks:
        ep_m = re.search(r'\u0627\u0644\u062d\u0644\u0642\u0629\s*(\d+)', etitle)
        ep_num = int(ep_m.group(1)) if ep_m else 0
        if ep_num:
            output['episodes'].append({'episodeNumber': ep_num, 'title': '\u062d\u0644\u0642\u0629 ' + str(ep_num), 'url': eurl})

# Save to file
with open('scripts/tuktukhd/debug_output.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("Saved to debug_output.json")
print("Genres:", output.get('genres', []))
print("Categories:", output.get('categories', []))
print("Seasons:", len(output.get('seasons', [])))
print("Episodes:", len(output.get('episodes', [])))