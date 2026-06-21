import json, os, re, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(BASE_DIR, exist_ok=True)

CAT = 'turkish-series'
BASE = 'https://tv8.egydead.live'

# ── Fetch with undetected-chromedriver to bypass Cloudflare ──
def fetch_page(url, retries=3):
    import undetected_chromedriver as uc
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    for attempt in range(retries):
        try:
            driver = uc.Chrome(options=options, version_main=120)
            driver.get(url)
            time.sleep(5)
            html = driver.page_source
            driver.quit()
            if 'Just a moment' not in html[:200]:
                return html
        except Exception as e:
            print(f'  Attempt {attempt+1} failed: {e}')
            try: driver.quit()
            except: pass
            time.sleep(3)
    return None

# ── Parse series from category page ──
def parse_category(html):
    import re
    series = []
    # Look for series blocks - links with poster images
    # Pattern: article/div with link to /series/XXX/ and poster image
    blocks = re.findall(
        r'<a\s+href="(/[^"]*/([^/]+)/?)"[^>]*>.*?<img[^>]+src="([^"]*)"[^>]*>.*?</a>',
        html, re.DOTALL
    )
    for href, slug, poster in blocks:
        title = slug.replace('-', ' ').strip()
        series.append({
            'title': title,
            'slug': slug,
            'url': BASE + href,
            'poster': poster,
        })
    # Fallback: more generic series links
    if not series:
        links = re.findall(r'<a\s+href="(/series/[^"]*)"[^>]*>([^<]*)</a>', html)
        for href, title in links:
            title = title.strip()
            if title:
                series.append({
                    'title': title,
                    'slug': href.split('/')[-1],
                    'url': BASE + href,
                    'poster': '',
                })
    return series

# ── Parse series page for episodes ──
def parse_series_page(html, series_title, poster):
    import re
    # Get description
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
    description = desc_match.group(1) if desc_match else ''
    
    # Get poster from og:image if not provided
    if not poster:
        og_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', html)
        if og_match:
            poster = og_match.group(1)
    
    # Get episodes
    episodes = []
    ep_links = re.findall(r'<a\s+href="(/episode/[^"]*)"[^>]*>([^<]*)</a>', html)
    for ep_href, ep_title in ep_links:
        ep_title = ep_title.strip()
        ep_num_match = re.search(r'(\d+)', ep_title)
        ep_num = int(ep_num_match.group(1)) if ep_num_match else 0
        episodes.append({
            'episodeNumber': ep_num,
            'title': ep_title,
            'url': BASE + ep_href,
        })
    
    return {
        'title': series_title,
        'description': description,
        'poster': poster,
        'episodes': episodes,
    }

# ── Parse episode page for servers ──
def parse_episode(ep):
    import re, undetected_chromedriver as uc
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    try:
        driver = uc.Chrome(options=options, version_main=120)
        driver.get(ep['url'])
        time.sleep(5)
        html = driver.page_source
        driver.quit()
        
        servers = []
        # Look for iframe/data-embed-url/server links
        embed_urls = re.findall(r'data-embed-url="([^"]*)"', html)
        iframe_urls = re.findall(r'<iframe[^>]+src="([^"]*)"', html)
        for url in embed_urls + iframe_urls:
            is_def = 'vidspeed' in url or len(servers) == 0
            servers.append({
                'name': f'Server {len(servers)+1}',
                'url': url,
                'isDefault': is_def,
            })
        
        return {
            'episodeNumber': ep['episodeNumber'],
            'title': ep['title'],
            'duration': '',
            'servers': servers,
            'downloadServers': [],
        }
    except Exception as e:
        print(f'    Error: {e}')
        return None

# ═══════════════════════════════
# MAIN
# ═══════════════════════════════
def main():
    output_file = os.path.join(BASE_DIR, f'{CAT}.json')
    
    # Step 1: Fetch category page
    print(f'Fetching category page: {BASE}/series-category/{CAT}/')
    html = fetch_page(f'{BASE}/series-category/{CAT}/')
    if not html:
        print('Failed to fetch category page')
        return
    
    # Step 2: Parse series list
    series_list = parse_category(html)
    print(f'Found {len(series_list)} series')
    for s in series_list[:5]:
        print(f'  {s["title"]} - {s["url"][:60]}')
    
    if len(series_list) > 5:
        print(f'  ... and {len(series_list)-5} more')
    
    # Just test with first series for now
    if series_list:
        s = series_list[0]
        print(f'\nFetching series page: {s["title"]}')
        html2 = fetch_page(s['url'])
        if html2:
            parsed = parse_series_page(html2, s['title'], s['poster'])
            print(f'  Episodes: {len(parsed["episodes"])}')
            for ep in parsed['episodes'][:3]:
                print(f'    Ep {ep["episodeNumber"]}: {ep["title"]}')
            print(f'  Description: {parsed["description"][:100]}')
            print(f'  Poster: {parsed["poster"][:80]}')
            
            # Fetch first episode's servers
            if parsed['episodes']:
                ep0 = parsed['episodes'][0]
                print(f'\nFetching episode page for server data...')
                ep_data = parse_episode(ep0)
                if ep_data:
                    print(f'  Servers: {len(ep_data["servers"])}')
                    for sv in ep_data['servers'][:3]:
                        print(f'    {sv["name"]}: {sv["url"][:60]}')

if __name__ == '__main__':
    main()
