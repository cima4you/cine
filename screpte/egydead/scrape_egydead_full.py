import sys, time, json, os, re, traceback
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://tv8.egydead.live'
OUTPUT = r'D:\Users\DT01\Desktop\rachid-site\scripts\egydead\egydead.json'
PROGRESS = r'D:\Users\DT01\Desktop\rachid-site\scripts\egydead\egydead_progress.json'
MAX_PAGES = 121

import undetected_chromedriver as uc

def fetch_category(driver, page):
    url = f'{BASE_URL}/series-category/turkish-series/'
    if page > 1: url += f'?page={page}/'
    result = driver.execute_script(f'''
        return fetch('{url}', {{method:'GET', headers:{{'Accept':'text/html'}}}})
        .then(r => r.text())
        .then(html => {{
            const items = [];
            const regex = /<li class="movieItem">(.*?)<\\/li>/gs;
            let m;
            while ((m = regex.exec(html)) !== null) {{
                const h = m[1];
                const a = h.match(/<a\\s+href="([^"]*)"\\s+title="([^"]*)"/);
                if (!a) continue;
                const img = h.match(/<img[^>]+src="([^"]*)"/);
                const h1 = h.match(/<h1[^>]*>([^<]+)<\\/h1>/);
                const ep = h.match(/number_episode[^>]*>[^<]*<[^>]*>[^<]+<\\/[^>]*>[^<]*<em>(\\d+)<\\/em>/);
                const lbl = h.match(/class="label"[^>]*>([^<]+)<\\//);
                const cat = h.match(/class="cat_name"[^>]*>([^<]+)<\\//);
                items.push({{
                    title: a[2], url: a[1],
                    image: img ? img[1] : '',
                    h1: h1 ? h1[1] : '',
                    epNum: ep ? ep[1] : '',
                    label: lbl ? lbl[1] : '',
                    category: cat ? cat[1] : '',
                    servers: []
                }});
            }}
            return items;
        }})
        .catch(e => ({{error: e.toString()}}));
    ''')
    return result

def fetch_servers_batch(driver, urls):
    """Fetch multiple episodes concurrently in browser with individual timeouts"""
    urls_json = json.dumps(urls)
    result = driver.execute_script(f'''
        const urls = {urls_json};
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 8000);
        return Promise.all(urls.map(url =>
            fetch(url, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                body: 'View=1',
                signal: controller.signal
            }})
            .then(r => r.text())
            .then(html => ({{
                url: url,
                servers: (() => {{
                    const sr = /<li[^>]*data-link="([^"]*)"[^>]*>.*?<p>([^<]*)<\\/p>/gs;
                    const s = []; let m;
                    while ((m = sr.exec(html)) !== null) s.push({{name: m[2], url: m[1]}});
                    return s;
                }})(),
                description: (html.match(/<meta\\s+name="description"\\s+content="([^"]*)"/) || [])[1] || '',
                cover: (html.match(/singleCover[^>]*style="background-image:\\s*url\\(([^)]+)\\)/) || [])[1] || '',
                date: (html.match(/postDate[^>]*>([^<]+)</) || [])[1] || '',
                views: (html.match(/fa-eye<\\/i><em>(\\d+)<\\/em>/) || [])[1] || ''
            }}))
            .catch(e => ({{url: url, error: e.toString()}}))
        )).finally(() => clearTimeout(timeout));
    ''')
    return result

# ===== MAIN =====
print('='*60)
print('EgyDead Full Scraper - All 121 Pages')
print('='*60)

options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')
driver = uc.Chrome(options=options, version_main=148)

all_episodes = []

# Resume from progress file if exists
if os.path.exists(PROGRESS):
    with open(PROGRESS, 'r', encoding='utf-8') as f:
        saved = json.load(f)
    skip = saved.get('processed', 0)
    all_episodes = saved['episodes']
    print(f'Resuming: {skip}/{saved["total"]} already processed ({saved["success"]} with servers)')
else:
    skip = 0

try:
    if skip == 0:
        # Cloudflare bypass
        print('\nBypassing Cloudflare...')
        driver.get(f'{BASE_URL}/')
        time.sleep(25)
        
        # ===== PHASE 1: Scrape all category pages =====
        print(f'\n{"="*60}')
        print(f'PHASE 1: Scraping {MAX_PAGES} pages...')
        t1 = time.time()
        
        for page in range(1, MAX_PAGES + 1):
            result = fetch_category(driver, page)
            if isinstance(result, list) and len(result) > 0:
                all_episodes.extend(result)
                print(f'  Page {page:3d}: {len(result):2d} episodes (total: {len(all_episodes):5d})')
            else:
                print(f'  Page {page:3d}: {"ERROR" if isinstance(result, dict) else "empty"}')
            
            if page % 20 == 0:
                with open(PROGRESS, 'w', encoding='utf-8') as f:
                    json.dump({'page': page, 'total': len(all_episodes), 'episodes': all_episodes}, f, ensure_ascii=False)
        
        elapsed = time.time() - t1
        print(f'\nPhase 1 done: {len(all_episodes)} episodes in {elapsed:.0f}s')
    else:
        t1 = time.time()
        print(f'Skipping Phase 1 (resuming from {skip}/{len(all_episodes)})')
    
    if len(all_episodes) == 0:
        print('No episodes found. Aborting.')
        driver.quit()
        sys.exit(1)
    
    # ===== PHASE 2: Fetch servers for ALL episodes =====
    print(f'\n{"="*60}')
    print(f'PHASE 2: Fetching servers for {len(all_episodes)} episodes...')
    t2 = time.time()
    
    BATCH_SIZE = 3
    success = sum(1 for e in all_episodes[:skip] if e.get('servers'))
    fail = skip - sum(1 for e in all_episodes[:skip] if e.get('servers'))
    
    # Set script timeout
    driver.set_script_timeout(15)
    
    for batch_start in range(skip, len(all_episodes), BATCH_SIZE):
        batch = all_episodes[batch_start:batch_start + BATCH_SIZE]
        urls = [ep['url'] for ep in batch]
        
        try:
            results = fetch_servers_batch(driver, urls)
        except Exception:
            # Timeout on the whole batch - mark all as failed
            for ep in batch:
                fail += 1
            batch_end = min(batch_start + BATCH_SIZE, len(all_episodes))
            print(f'  [{batch_end}/{len(all_episodes)}] BATCH TIMEOUT ❌ fail={fail}')
            time.sleep(1)
            continue
        
        for ep, data in zip(batch, results):
            if 'error' not in data:
                ep['servers'] = data.get('servers', [])
                ep['description'] = ep.get('description') or data.get('description', '')
                ep['cover'] = ep.get('cover') or data.get('cover', '')
                ep['date'] = ep.get('date') or data.get('date', '')
                ep['views'] = ep.get('views') or data.get('views', '')
                if len(data.get('servers', [])) > 0:
                    success += 1
                else:
                    pass
            else:
                fail += 1
        
        batch_end = min(batch_start + BATCH_SIZE, len(all_episodes))
        print(f'  [{batch_end}/{len(all_episodes)}] ✅ success={success} ❌ fail={fail}', end='\r')
        
        # Save progress every 200 episodes
        if batch_end % 200 == 0:
            with open(PROGRESS, 'w', encoding='utf-8') as f:
                json.dump({
                    'page': 'done',
                    'processed': batch_end,
                    'total': len(all_episodes),
                    'success': success,
                    'fail': fail,
                    'episodes': all_episodes
                }, f, ensure_ascii=False)
            print(f'\n  [PROGRESS] Saved at episode {batch_end}/{len(all_episodes)}')
        
        time.sleep(0.3)
    
    print()
    elapsed2 = time.time() - t2
    print(f'\nPhase 2 done: {success} with servers, {fail} failed in {elapsed2:.0f}s')
    
    # ===== SAVE FINAL =====
    # Clean up - remove series_name field and add it
    for ep in all_episodes:
        name = ep.get('title', '')
        name = re.sub(r'\s+الحلقة\s+\d+.*$', '', name)
        name = re.sub(r'\s+مدبلج\s+كامل$', '', name)
        name = re.sub(r'\s+مترجم\s+كامل$', '', name)
        name = re.sub(r'\s+الاخيرة$', '', name)
        ep['series_name'] = name.strip()
    
    # Extract year
    for ep in all_episodes:
        text = (ep.get('description','') or '') + ' ' + ep.get('title','')
        years = re.findall(r'\b(20\d{2})\b', text)
        ep['year'] = next((y for y in years if 2020 <= int(y) <= 2030), '')
    
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(all_episodes, f, ensure_ascii=False, indent=2)
    
    # Stats
    total_servers = sum(len(ep.get('servers',[])) for ep in all_episodes)
    with_servers = sum(1 for ep in all_episodes if ep.get('servers'))
    unique_series = len(set(ep.get('series_name','') for ep in all_episodes))
    
    print(f'\n{"="*60}')
    print(f'FINAL SUMMARY')
    print(f'  File: {OUTPUT}')
    print(f'  Total pages: {MAX_PAGES}')
    print(f'  Total episodes: {len(all_episodes)}')
    print(f'  Unique series: ~{unique_series}')
    print(f'  Episodes with servers: {with_servers}')
    print(f'  Total server links: {total_servers}')
    print(f'  Total time: {(time.time()-t1)/60:.1f} minutes')
    
    # Remove progress file
    if os.path.exists(PROGRESS):
        os.remove(PROGRESS)

finally:
    driver.quit()
