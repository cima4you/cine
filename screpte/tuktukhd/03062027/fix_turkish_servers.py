import json, re, html, requests, base64, concurrent.futures

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Multi-quality Turkish
multi = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي'
         and any('متعدد' in s.get('name','') or 'جودة' in s.get('name','') for s in (x.get('servers') or []))]
no_srv = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي'
          and not x.get('servers')]

print('Multi-quality: {}'.format(len(multi)))
for idx, item in multi:
    servers = [s.get('name','') for s in (item.get('servers') or [])]
    print('  idx={}: "{}" ({}) -> {}'.format(idx, item.get('title','').strip()[:50], item.get('year',''), servers))

print('\nNo servers: {}'.format(len(no_srv)))
for idx, item in no_srv:
    print('  idx={}: "{}" ({})'.format(idx, item.get('title','').strip()[:50], item.get('year','')))

# Try to find them on tuktukhd via direct search
all_problems = multi + no_srv
if all_problems:
    print('\nTrying to find tuktukhd URLs...')
    
    with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
        sitemap = json.load(f)
    with open('scripts/tuktukhd/data/tuktuk_anime_index_v3.json', 'r', encoding='utf-8') as f:
        anime_idx = json.load(f)
    with open('scripts/tuktukhd/data/turkish_listing.json', 'r', encoding='utf-8') as f:
        listing = json.load(f)
    
    all_idx = sitemap + anime_idx
    for m in listing:
        all_idx.append({'name': m['name'], 'year': m['year'], 'url': m['url']})
    
    def super_norm(t):
        t = t.lower().strip()
        t = t.replace('ü','u').replace('ğ','g').replace('ş','s').replace('ı','i').replace('ö','o').replace('ç','c')
        t = re.sub(r"\s+\d{4}$", '', t)
        t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
        t = re.sub(r'\s+', '', t)
        return t.strip()
    
    from difflib import SequenceMatcher
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    found = []
    
    for idx, item in all_problems:
        title = html.unescape(item.get('title', '').strip())
        year = str(item.get('year', ''))
        tn = super_norm(title)
        
        best = None
        best_score = 0
        for s in all_idx:
            yr_diff = abs(int(s['year']) - int(year)) if s['year'].isdigit() and year.isdigit() else 99
            if yr_diff > 2:
                continue
            s_sn = super_norm(s['name'])
            score = SequenceMatcher(None, tn, s_sn).ratio()
            if score > best_score and score > 0.7:
                best_score = score
                best = s
        
        if best:
            found.append({'idx': idx, 'title': title, 'year': year, 'url': best['url'], 'score': best_score})
            print('  FOUND: "{}" ({}) score={:.2f}'.format(title[:40], year, best_score))
        else:
            print('  NOT FOUND: "{}" ({})'.format(title[:40], year))
    
    if found:
        print('\nFetching server data for found...')
        def fetch_and_update(m):
            try:
                r = requests.get(m['url'], timeout=20, headers=headers)
                crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
                watch_urls = []
                for c in crypts:
                    try:
                        watch_urls.append(base64.b64decode(c).decode('utf-8'))
                    except:
                        pass
                dl_links = re.findall(r'data-real-url="([^"]+)"', r.text)
                si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', r.text, re.DOTALL)
                
                if not watch_urls:
                    return {'idx': m['idx'], 'success': False}
                
                new_servers = []
                for i, wu in enumerate(watch_urls):
                    sname = si[i].strip() if i < len(si) else ('TukTuk Vip' if i == 0 else 'TukTuk {}'.format(i + 1))
                    new_servers.append({'name': sname, 'url': wu, 'isDefault': i == 0})
                for dl in dl_links:
                    new_servers.append({'name': 'Download', 'url': dl, 'isDefault': False})
                
                # Also poster
                poster = ''
                pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', r.text)
                if pm:
                    poster = pm.group(1)
                
                return {'idx': m['idx'], 'servers': new_servers, 'poster': poster, 'success': True}
            except:
                return {'idx': m['idx'], 'success': False}
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(fetch_and_update, m) for m in found]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        updated = 0
        for r in results:
            if r.get('success') and r.get('servers'):
                idx = r['idx']
                d[idx]['servers'] = r['servers']
                if r.get('poster') and not d[idx].get('poster','').startswith('https://tuktukhd'):
                    d[idx]['poster'] = r['poster']
                updated += 1
                print('  UPDATED: "{}"'.format(d[idx].get('title','').strip()[:50]))
        
        if updated > 0:
            prefix = content[:content.index('[')]
            suffix = content[content.rindex(']') + 1:]
            with open('data.js', 'w', encoding='utf-8') as f:
                f.write(prefix + json.dumps(d, ensure_ascii=False) + suffix)
            print('\nUpdated: {} movies'.format(updated))
