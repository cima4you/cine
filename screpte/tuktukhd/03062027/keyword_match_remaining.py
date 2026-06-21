import requests, re, json, concurrent.futures, base64
from difflib import SequenceMatcher

headers = {'User-Agent': 'Mozilla/5.0'}

# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

# Load all indexes
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)
cat_file = 'scripts/tuktukhd/data/tuktuk_other_categories.json'
try:
    with open(cat_file, 'r', encoding='utf-8') as f:
        cats = json.load(f)
except:
    cats = []
combined = sitemap + cats

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

remaining = []
for idx, item in enumerate(data_js):
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        remaining.append({
            'idx': idx, 'title': item.get('title', '').strip(),
            'year': str(item.get('year', '')), 'type': item.get('type', '')
        })

print('Remaining: {}'.format(len(remaining)))

def norm(t):
    t = t.lower().strip()
    t = t.replace('ü', 'u').replace('Ü', 'u')
    t = t.replace('ğ', 'g').replace('Ğ', 'g')
    t = t.replace('ş', 's').replace('Ş', 's')
    t = t.replace('ı', 'i').replace('I', 'i')
    t = t.replace('ö', 'o').replace('Ö', 'o')
    t = t.replace('ç', 'c').replace('Ç', 'c')
    t = t.replace('è', 'e').replace('é', 'e').replace('ê', 'e').replace('ë', 'e')
    t = t.replace('à', 'a').replace('á', 'a').replace('â', 'a').replace('ã', 'a')
    t = t.replace('ì', 'i').replace('í', 'i').replace('î', 'i')
    t = t.replace('ò', 'o').replace('ó', 'o').replace('ô', 'o').replace('õ', 'o')
    t = t.replace('ù', 'u').replace('ú', 'u').replace('û', 'u')
    t = t.replace('ū', 'u').replace('ō', 'o')
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

def get_keywords(t):
    """Extract meaningful keywords from a title"""
    t = t.lower().strip()
    t = re.sub(r'\s+\d{4}$', '', t)
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    words = t.split()
    # Remove short words and pure numbers
    return [w for w in words if len(w) >= 3 and not re.match(r'^\d+$', w)]

def keyword_match_score(r_title, r_year, s_title, s_year):
    """Score based on shared keywords"""
    r_words = set(get_keywords(r_title))
    s_words = set(get_keywords(s_title))
    
    if not r_words or not s_words:
        return 0
    
    # Count how many r_words appear in ANY form within any s_word
    matches = 0
    for rw in r_words:
        rn = norm(rw)
        for sw in s_words:
            sn = norm(sw)
            if rn == sn or (len(rn) >= 4 and len(sn) >= 4 and (rn in sn or sn in rn)):
                matches += 1
                break
    
    if matches == 0:
        return 0
    
    score = matches / len(r_words)
    # Bonus for year match
    yr_diff = abs(int(r_year) - int(s_year)) if r_year.isdigit() and s_year.isdigit() else 99
    if yr_diff <= 1:
        score += 0.1
    
    return score

matched = []
unmatched = []

for item in remaining:
    r_title = item['title']
    r_year = item['year']
    best = None
    best_score = 0
    best_method = ''
    
    # Strategy 1: keyword match
    for s in combined:
        yr_diff = abs(int(r_year) - int(s['year'])) if r_year.isdigit() and s['year'].isdigit() else 99
        if yr_diff > 1:
            continue
        
        ks = keyword_match_score(r_title, r_year, s['name'], s['year'])
        if ks > best_score and ks >= 0.4:
            best_score = ks
            best = s
            best_method = 'keyword'
    
    # Strategy 2: SequenceMatcher (for some English-Japanese matches)
    if not best or best_score < 0.5:
        for s in combined:
            yr_diff = abs(int(r_year) - int(s['year'])) if r_year.isdigit() and s['year'].isdigit() else 99
            if yr_diff > 1:
                continue
            
            rn = norm(r_title)
            sn = norm(s['name'])
            if len(rn) >= 5 and len(sn) >= 5:
                short, long_ = (rn, sn) if len(rn) <= len(sn) else (sn, rn)
                if short in long_:
                    sc = 0.85 + len(short) / max(len(rn), len(sn)) * 0.15
                else:
                    sc = SequenceMatcher(None, rn, sn).ratio()
            else:
                sc = 0
            
            if sc > best_score and sc >= 0.65:
                best_score = sc
                best = s
                best_method = 'seq'
    
    if best and best_score >= 0.4:
        matched.append({
            'idx': item['idx'], 'title': r_title, 'year': r_year,
            'type': item['type'], 'url': best['url'],
            'match_title': best['name'], 'match_year': best['year'],
            'score': round(best_score, 3), 'method': best_method
        })
    else:
        unmatched.append(item)

print('Matched: {}'.format(len(matched)))
print('Unmatched: {}'.format(len(unmatched)))

if matched:
    print('\nMatched items:')
    for m in sorted(matched, key=lambda x: -x['score']):
        print('  "{}" ({}) -> "{}" ({}) [{:.3f}] {} [{}]'.format(
            m['title'], m['year'], m['match_title'], m['match_year'], m['score'], m['type'], m['method']))

if unmatched:
    print('\nStill unmatched:')
    for m in unmatched:
        print('  "{}" ({}) [{}]'.format(m['title'], m['year'], m['type']))

if matched:
    print('\nVisiting {} pages...'.format(len(matched)))
    
    def extract(item):
        try:
            r = requests.get(item['url'], timeout=20, headers=headers)
            crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
            watch_urls = [base64.b64decode(c).decode('utf-8') for c in crypts]
            dl_links = re.findall(r'data-real-url="([^"]+)"', r.text)
            si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', r.text, re.DOTALL)
            sname = si[0].strip() if si else 'TukTuk Vip'
            return {
                'idx': item['idx'], 'title': item['title'],
                'watch_url': watch_urls[0] if watch_urls else None,
                'server_name': sname,
                'download_urls': dl_links,
                'success': len(watch_urls) > 0
            }
        except Exception as e:
            return {'idx': item['idx'], 'success': False, 'error': str(e)}
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(extract, m) for m in matched]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    successful = [r for r in results if r.get('success')]
    print('Success: {}, Failed: {}'.format(len(successful), len(results) - len(successful)))
    
    updated = 0
    for r in successful:
        idx = r['idx']
        item = data_js[idx]
        new_server = {'name': r['server_name'], 'url': r['watch_url'], 'isDefault': True}
        new_downloads = [{'name': 'TukTuk Download', 'url': dl} for dl in r.get('download_urls', [])]
        old_servers = item.get('servers', [])
        item['servers'] = [s for s in old_servers if s.get('name', '') not in target_servers]
        item['servers'].insert(0, new_server)
        if new_downloads:
            item['downloadServers'] = new_downloads
        updated += 1
    
    print('Updated: {} items'.format(updated))
    
    if updated > 0:
        prefix = content[:content.index('[')]
        suffix = content[content.rindex(']') + 1:]
        json_str = json.dumps(data_js, ensure_ascii=False)
        with open('data.js', 'w', encoding='utf-8') as f:
            f.write(prefix + json_str + suffix)
        print('Saved data.js')
    
    final_remaining = sum(1 for item in data_js if any(s.get('name', '') in target_servers for s in item.get('servers', [])))
    print('Final remaining multi-quality servers: {}'.format(final_remaining))
