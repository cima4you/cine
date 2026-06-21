import requests, re, json, concurrent.futures, base64
from difflib import SequenceMatcher

headers = {'User-Agent': 'Mozilla/5.0'}

# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

# Load sitemap + category listings
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

cat_file = 'scripts/tuktukhd/data/tuktuk_other_categories.json'
try:
    with open(cat_file, 'r', encoding='utf-8') as f:
        cats = json.load(f)
except:
    cats = []

combined = sitemap + cats
print('Combined index: {} entries'.format(len(combined)))

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

remaining = []
for idx, item in enumerate(data_js):
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        remaining.append({
            'idx': idx, 'title': item.get('title', '').strip(),
            'year': str(item.get('year', '')), 'type': item.get('type', '')
        })

print('Items needing update: {}'.format(len(remaining)))

# Better normalization: Turkish chars, more unicode normalization
def norm(t):
    t = t.lower().strip()
    # Normalize Turkish and accented characters
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
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

def make_key(title, year):
    """Normalized key for exact matching"""
    t = norm(title)
    return t, year

def title_similarity(a_title, a_year, b_title, b_year):
    """Compute similarity with year-aware normalization"""
    an = norm(a_title)
    bn = norm(b_title)
    
    if not an or not bn:
        return 0
    
    # Quick exact match
    if an == bn:
        return 1.0
    
    # Substring check - only if short side >= 5 chars
    short, long_ = (an, bn) if len(an) <= len(bn) else (bn, an)
    if len(short) >= 5 and short in long_:
        return 0.85 + len(short) / max(len(an), len(bn)) * 0.15
    
    # Try without the year component in the title name
    # Some titles like "Malazgirt 1071" have a number that looks like a year
    # Strip numbers from one and compare
    an_no_num = re.sub(r'\d+', '', an)
    bn_no_num = re.sub(r'\d+', '', bn)
    if an_no_num and bn_no_num:
        short2, long2 = (an_no_num, bn_no_num) if len(an_no_num) <= len(bn_no_num) else (bn_no_num, an_no_num)
        if len(short2) >= 5 and short2 in long2:
            return 0.80 + len(short2) / max(len(an_no_num), len(bn_no_num)) * 0.15
    
    return SequenceMatcher(None, an, bn).ratio()

matched = []
unmatched = []

for item in remaining:
    r_title = item['title']
    r_year = item['year']
    best = None
    best_score = 0
    
    for s in combined:
        s_title = s['name']
        s_year = s['year']
        
        yr_diff = abs(int(r_year) - int(s_year)) if r_year.isdigit() and s_year.isdigit() else 999
        if yr_diff > 1:
            continue
        
        score = title_similarity(r_title, r_year, s_title, s_year)
        min_score = 0.75 if yr_diff == 0 else 0.80
        
        if score > best_score and score > min_score:
            best_score = score
            best = s
    
    if best and best_score >= 0.72:
        matched.append({
            'idx': item['idx'], 'title': r_title, 'year': r_year,
            'type': item['type'], 'url': best['url'],
            'match_title': best['name'], 'match_year': best['year'],
            'score': round(best_score, 3)
        })
    else:
        unmatched.append(item)

print('Matched: {}'.format(len(matched)))
print('Unmatched: {}'.format(len(unmatched)))

if matched:
    print('\nMatched items:')
    for m in sorted(matched, key=lambda x: -x['score']):
        print('  "{}" ({}) -> "{}" ({}) [{:.3f}] {}'.format(
            m['title'], m['year'], m['match_title'], m['match_year'], m['score'], m['type']))

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
