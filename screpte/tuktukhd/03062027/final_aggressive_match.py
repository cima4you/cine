import requests, re, json, concurrent.futures, base64, time
from difflib import SequenceMatcher

headers = {'User-Agent': 'Mozilla/5.0'}

# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

# Load sitemap index
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

# Find remaining items needing update
remaining = []
for idx, item in enumerate(data_js):
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        remaining.append({
            'idx': idx,
            'title': item.get('title', '').strip(),
            'year': str(item.get('year', '')),
            'type': item.get('type', '')
        })

print('Remaining items: {}'.format(len(remaining)))

def super_norm(t):
    t = t.lower().strip()
    t = re.sub(r'\s+\d{4}$', '', t)
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

def title_similarity(a, b):
    a = super_norm(a)
    b = super_norm(b)
    if not a or not b:
        return 0
    if a == b:
        return 1.0
    # Only allow substring match if the shorter string is at least 5 chars
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    if len(short) >= 5 and short in long_:
        return 0.85 + len(short) / max(len(a), len(b)) * 0.15
    return SequenceMatcher(None, a, b).ratio()

# Search sitemap for each remaining item
matched = []
unmatched = []

for item in remaining:
    r_title = item['title']
    r_year = item['year']
    r_norm = super_norm(r_title)
    
    best = None
    best_score = 0
    
    for s in sitemap:
        s_title = s['name']
        s_year = s['year']
        s_norm = super_norm(s_title)
        
        # Check if same year or year difference ≤ 1
        year_diff = abs(int(r_year) - int(s_year)) if r_year.isdigit() and s_year.isdigit() else 999
        
        if year_diff > 1:
            continue
        
        score = title_similarity(r_title, s_title)
        
        # Only consider if the score is good enough
        min_score = 0.75 if year_diff == 0 else 0.85
        
        if score > best_score and score > min_score:
            best_score = score
            best = s
    
    if best and best_score > 0.75:
        matched.append({
            'idx': item['idx'],
            'title': r_title,
            'year': r_year,
            'type': item['type'],
            'url': best['url'],
            'match_title': best['name'],
            'match_year': best['year'],
            'score': best_score
        })
    else:
        unmatched.append(item)

print('Matched: {}'.format(len(matched)))
print('Unmatched: {}'.format(len(unmatched)))

if matched:
    print('\nMatched items:')
    for m in sorted(matched, key=lambda x: -x['score']):
        print('  "{}" ({}) -> "{}" ({}) [{:.2f}] {}'.format(
            m['title'], m['year'], m['match_title'], m['match_year'], m['score'], m['type']))

if unmatched:
    print('\nTruly unmatched:')
    for m in unmatched:
        print('  "{}" ({}) [{}]'.format(m['title'], m['year'], m['type']))

if matched:
    # Visit pages
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
    
    # Update
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
