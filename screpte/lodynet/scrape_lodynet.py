#!/usr/bin/env python3
"""
LodyNet Watch Scraper - Turkish Series
=======================================
Usage:
  python scrape_lodynet.py                    # Scrape all pages
  python scrape_lodynet.py --start 1 --end 5   # Scrape pages 1 to 5 only
  python scrape_lodynet.py --series-only       # Only get series list, not episodes

Controls:
  --start PAGE     First category page to scrape (default: 1)
  --end PAGE       Last category page (default: all)
  --series-only    Fetch series list only, skip episode server fetching
  --output FILE    Output file (default: lodynet_data.json)
  --format FILE    Output formatted file (default: lodynet_formatted.json)
  --resume         Resume from existing output file
"""

import sys, time, json, os, re, base64
sys.stdout.reconfigure(encoding='utf-8')

import undetected_chromedriver as uc

BASE_URL = 'https://lodynet.watch'
CATEGORY_URL = BASE_URL + '/category/%D9%85%D8%B4%D8%A7%D9%87%D8%AF%D8%A9-%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%AA%D8%B1%D9%83%D9%8A%D8%A9/'
AJAX_URL = f'{BASE_URL}/wp-content/themes/Lodynet2020/Api/RequestExpansion.php'
CATEGORY_ID = '36'  # Turkish series

# ==================== PARSING HELPERS ====================

def parse_initial_page(html):
    """Parse series items from initial page HTML"""
    items = []
    # Try embedded JSON first
    m = re.search(r'var TheRequesterData\s*=\s*({.*?});', html, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            for item in data.get('Items', []):
                items.append({
                    'name': item.get('name', ''),
                    'url': item.get('url', '').replace('\\/', '/'),
                    'cover': item.get('cover', '').replace('\\/', '/'),
                    'slug': item.get('slug', ''),
                    'ID': item.get('ID', ''),
                    'count': item.get('count', 0),
                    'ribbon': item.get('ribbon', ''),
                    'episode': item.get('episode', 0)
                })
            return items
        except:
            pass
    
    # Fallback: parse HTML
    # Count items
    item_count = len(re.findall(r'<div class="ItemNewly">', html))
    json_count = len(re.findall(r'TheRequesterData', html))
    print(f'      HTML items found: {item_count}, JSON found: {json_count}')
    
    for item_html in re.finditer(r'<div class="ItemNewly">.*?</div>\s*</div>', html, re.DOTALL):
        h = item_html.group(0)
        a = re.search(r'<a\s+title="([^"]*)"\s+href="([^"]*)"', h)
        if not a: continue
        cover = re.search(r'data-src="([^"]*)"', h)
        episode = re.search(r'حلقة رقم </small>(\d+)</div>', h)
        ribbon = re.search(r'<div class="NewlyRibbon">([^<]+)</div>', h)
        items.append({
            'name': a.group(1),
            'url': a.group(2),
            'cover': cover.group(1) if cover else '',
            'episode': int(episode.group(1)) if episode else 0,
            'ribbon': ribbon.group(1) if ribbon else ''
        })
    return items

def parse_ajax_items(response):
    """Parse series items from AJAX JSON response"""
    items = []
    for item in response.get('Items', []):
        items.append({
            'name': item.get('name', ''),
            'url': (BASE_URL + item['url']) if item.get('url', '').startswith('/') else item.get('url', ''),
            'cover': (BASE_URL + item['cover']) if item.get('cover', '').startswith('/') else item.get('cover', ''),
            'episode': item.get('episode', 0),
            'ribbon': item.get('ribbon', '')
        })
    return items, response.get('Recall', False)

def decode_base64_url(s):
    """Decode string if it looks like base64"""
    if not s: return s
    try:
        decoded = base64.b64decode(s).decode('utf-8')
        if decoded.startswith('http'):
            return decoded
    except:
        pass
    return s

def parse_episode_servers(html):
    """Extract server URLs from episode page HTML"""
    # Find PostData.ServersWatch
    m = re.search(r'ServersWatch:\s*(\[.*?\])', html, re.DOTALL)
    if not m: return []
    
    try:
        servers = json.loads(m.group(1))
    except:
        return []
    
    result = []
    for s in servers:
        embed = s.get('Embed', '')
        name = s.get('Name', '')
        # Decode base64 regardless of Encrypted flag
        embed = decode_base64_url(embed)
        if embed:
            result.append({'name': name, 'url': embed})
    
    return result

def parse_download_servers(html):
    """Extract download server URLs from #DownloadArea"""
    result = []
    for a in re.finditer(r'<a\s+class="ItemServerDownload"[^>]*href="([^"]*)"[^>]*title="([^"]*)"', html):
        url = a.group(1)
        quality = a.group(2)
        if url:
            result.append({'name': quality, 'url': url})
    return result

def extract_episode_number(html, title):
    """Extract episode number from various sources"""
    # Try EpisodeNumber JS variable
    m = re.search(r'EpisodeNumber\s*=\s*(\d+)', html)
    if m: return int(m.group(1))
    
    # Try extracting from title: "الحلقة 6" or "الحلقة 10"
    m = re.search(r'الحلقة\s*(\d+)', title)
    if m: return int(m.group(1))
    
    # Try from URL
    m = re.search(r'الحلقة[_-](\d+)', html[:2000])
    if m: return int(m.group(1))
    
    return 0

def extract_series_info(html):
    """Extract year and description from episode/series page"""
    info = {'year': '', 'description': ''}
    
    # Find year - look for 1900-2029 in the title or meta
    m = re.search(r'<title>[^<]*((?:19|20)\d{2})[^<]*</title>', html)
    if m: info['year'] = m.group(1)
    
    if not info['year']:
        m = re.search(r'(?:19|20)\d{2}', html[:5000])
        if m: info['year'] = m.group(0)
    
    m = re.search(r'<div[^>]*id="ContentDetails"[^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        info['description'] = text[:500]
    
    return info

def clean_series_name(name):
    """Extract base series name from episode title"""
    # "مسلسل XYZ مترجم الحلقة 1" -> "مسلسل XYZ"
    name = re.sub(r'\s+الحلقة\s+\d+.*$', '', name)
    name = re.sub(r'\s+مترجم\s*$', '', name)
    name = re.sub(r'\s+مدبلج\s*$', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

# ==================== SCRAPING FUNCTIONS ====================

def scrape_all_series(driver, start_page=1, end_page=None):
    """Scrape all series from category pages via AJAX"""
    all_items = []
    page = 1
    has_more = True
    recall = True
    
    print(f'Scraping category pages (start={start_page}, end={end_page or "all"})...')
    
    while has_more:
        if end_page and page > end_page:
            break
        
        if page == 1:
            # First page: scrape HTML
            print(f'  Page 1: loading category page...')
            driver.get(CATEGORY_URL)
            time.sleep(5)
            html = driver.page_source
            html_len = len(html)
            print(f'    HTML size: {html_len} bytes')
            # Debug: save HTML if suspicious
            if args.debug or html_len < 5000:
                with open('debug_page1.html', 'w', encoding='utf-8') as f:
                    f.write(html[:50000])
                print(f'    Saved debug_page1.html ({min(html_len, 50000)} bytes)')
            items = parse_initial_page(html)
            all_items.extend(items)
            print(f'    Found {len(items)} items (total: {len(all_items)})')
            has_more = len(items) > 0  # If first page has items, there are likely more
            page = 2
        else:
            # Pages 2+: use AJAX
            print(f'  Page {page}: sending AJAX...', end=' ')
            result = driver.execute_script(f'''
                return new Promise((resolve) => {{
                    var fd = new FormData();
                    fd.append('indicator', {page});
                    fd.append('type', 'Categories');
                    fd.append('id', '{CATEGORY_ID}');
                    fetch('{AJAX_URL}', {{
                        method: 'POST',
                        body: fd
                    }})
                    .then(r => r.json())
                    .then(resolve)
                    .catch(e => resolve({{Error: e.toString()}}));
                }});
            ''')
            
            if isinstance(result, dict) and 'Error' in result:
                print(f'ERROR: {result["Error"]}')
                break
            
            items, recall = parse_ajax_items(result)
            all_items.extend(items)
            print(f'{len(items)} items (total: {len(all_items)})')
            
            if not recall:
                print(f'  No more pages (Recall=false)')
                break
            
            page += 1
            time.sleep(0.5)
    
    print(f'\nTotal series found: {len(all_items)}')
    return all_items

def fetch_page_via_js(driver, url, timeout=15):
    """Fetch a page using fetch() from within the browser session (no navigation needed)"""
    script = f'''
        return new Promise((resolve) => {{
            const controller = new AbortController();
            const t = setTimeout(() => controller.abort(), {timeout * 1000});
            fetch('{url}', {{
                method: 'GET',
                signal: controller.signal
            }})
            .then(r => r.text())
            .then(resolve)
            .catch(e => resolve(''));
        }});
    '''
    try:
        return driver.execute_script(script)
    except:
        return ''

def scrape_episodes_for_series(driver, series_items, output_path, resume=False):
    """For each series, fetch page via JS and extract all episode URLs with servers.
    Saves progress after each series to support resume."""
    results = []
    total = len(series_items)
    
    # Load existing progress if resuming
    processed_urls = set()
    if resume and os.path.exists(output_path):
        try:
            existing = json.load(open(output_path, 'r', encoding='utf-8'))
            results = existing
            for r in results:
                if r.get('url'):
                    processed_urls.add(r['url'])
            print(f'  Resuming: {len(results)} series already processed')
        except:
            pass
    
    for idx, series in enumerate(series_items):
        url = series.get('url', '')
        name = series.get('name', '')
        
        # Skip if already processed in resume mode
        if url in processed_urls:
            print(f'  [{idx+1}/{total}] {name[:40]}... SKIP (already done)')
            continue
        
        print(f'  [{idx+1}/{total}] {name[:40]}...', end=' ')
        
        # Fetch series/season page via JS (no navigation)
        html = fetch_page_via_js(driver, url)
        if not html:
            print('FAILED (empty page)')
            continue
        
        # Get episode items from this page
        episodes = []
        # Each episode on the series page is a div.ItemNewly
        for ep_html in re.finditer(r'<div class="ItemNewly">(.*?)</div>\s*</div>', html, re.DOTALL):
            h = ep_html.group(1)
            a = re.search(r'<a\s+title="([^"]*)"\s+href="([^"]*)"', h)
            if not a: continue
            ep_url = a.group(2)
            if not ep_url.startswith('http'):
                ep_url = BASE_URL + ep_url
            ep_title = a.group(1)
            cover = re.search(r'data-src="([^"]*)"', h)
            ep_num = re.search(r'حلقة رقم </small>(\d+)</div>', h)
            episodes.append({
                'title': ep_title,
                'url': ep_url,
                'cover': cover.group(1) if cover else '',
                'episodeNumber': extract_episode_number(h, ep_title),
                'servers': [],
                'downloadServers': []
            })
        
        if not episodes:
            # Try parsed JSON data (TheRequesterData)
            m = re.search(r'var TheRequesterData\s*=\s*({.*?});', html, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                    for item in data.get('Items', []):
                        ep_url = item.get('url', '').replace('\\/', '/')
                        if not ep_url.startswith('http'):
                            ep_url = BASE_URL + ep_url
                        episodes.append({
                            'title': item.get('name', ''),
                            'url': ep_url,
                            'cover': item.get('cover', '').replace('\\/', '/'),
                            'episodeNumber': extract_episode_number('', item.get('name', '')),
                            'servers': [],
                            'downloadServers': []
                        })
                except:
                    pass
        
        # If still no episodes, this might be an episode page itself; treat it as 1 episode
        if not episodes:
            servers = parse_episode_servers(html)
            download = parse_download_servers(html)
            ep_num = extract_episode_number(html, name)
            episodes.append({
                'title': name,
                'url': url,
                'cover': series.get('cover', ''),
                'episodeNumber': ep_num,
                'servers': servers,
                'downloadServers': download
            })
        
        # Sort episodes by episode number
        episodes.sort(key=lambda x: x['episodeNumber'])
        
        print(f'{len(episodes)} episodes', end='')
        
        # Fetch servers for each episode (skip those that already have them)
        success = 0
        for ep in episodes:
            if not ep['url']: continue
            if ep.get('servers') and len(ep['servers']) > 0:
                success += 1
                continue
            html2 = fetch_page_via_js(driver, ep['url'], timeout=15)
            if html2:
                servers = parse_episode_servers(html2)
                if servers:
                    ep['servers'] = servers
                    success += 1
                ep['downloadServers'] = parse_download_servers(html2)
            time.sleep(0.3)
        
        print(f' ({success} with servers)')
        
        # Extract series info (year, description) from first episode page
        series_info = extract_series_info(html)
        
        results.append({
            'name': name,
            'url': url,
            'cover': series.get('cover', ''),
            'year': series_info['year'],
            'description': series_info['description'],
            'episodes': episodes,
            'episodesWithServers': success,
            'totalEpisodes': len(episodes)
        })
        
        # Save progress after each series
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

# ==================== FORMAT CONVERTER ====================

def convert_to_standard_format(data):
    """Convert scraped data to standard format (series → seasons → episodes → servers)"""
    output = []
    
    def _sort_servers(arr):
        return sorted(arr, key=lambda x: (x.get('name', '') != 'Larhu', x.get('name', '')))

    for series in data:
        eps = series.get('episodes', [])
        if not eps: continue
        
        seasons = {1: []}
        for ep in eps:
            raw = ep.get('servers', [])
            servers = []
            for i, s in enumerate(_sort_servers(raw)):
                servers.append({
                    'name': s.get('name', f'server{i+1}'),
                    'url': s.get('url', ''),
                    'isDefault': i == 0
                })
            
            download_servers = []
            for s in ep.get('downloadServers', []):
                download_servers.append({
                    'name': s.get('name', ''),
                    'url': s.get('url', '')
                })
            
            seasons[1].append({
                'episodeNumber': ep.get('episodeNumber', 0),
                'title': ep.get('title', ''),
                'duration': '',
                'servers': servers,
                'downloadServers': download_servers
            })
        
        seasons[1].sort(key=lambda x: x['episodeNumber'])
        
        series_entry = {
            'title': series.get('name', ''),
            'originalName': '',
            'year': series.get('year', ''),
            'rating': '',
            'type': 'تركي',
            'contentType': 'series',
            'description': series.get('description', ''),
            'cast': [],
            'poster': series.get('cover', ''),
            'categories': ['مسلسلات تركية'],
            'quality': 'متعدد',
            'seasons': [{
                'seasonNumber': 1,
                'trial': '',
                'description': '',
                'poster': '',
                'episodes': seasons[1]
            }]
        }
        output.append(series_entry)
    
    output.sort(key=lambda x: x['title'])
    return output


# ==================== MAIN ====================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='LodyNet Turkish Series Scraper')
    parser.add_argument('--start', type=int, default=1, help='Start page (default: 1)')
    parser.add_argument('--end', type=int, default=None, help='End page (default: all)')
    parser.add_argument('--series-only', action='store_true', help='Only fetch series list')
    parser.add_argument('--output', default=r'D:\Users\DT01\Desktop\rachid-site\scripts\lodynet\lodynet_data.json', help='Output file')
    parser.add_argument('--format', default=r'D:\Users\DT01\Desktop\rachid-site\scripts\lodynet\lodynet_formatted.json', help='Formatted output file')
    parser.add_argument('--resume', action='store_true', help='Resume from existing output')
    parser.add_argument('--series-start', type=int, default=1, help='First series index to process (1-based)')
    parser.add_argument('--series-end', type=int, default=None, help='Last series index to process (default: all)')
    parser.add_argument('--debug', action='store_true', help='Save debug HTML files')
    
    args = parser.parse_args()
    
    print(f'CATEGORY_URL = {CATEGORY_URL}')
    print(f'AJAX_URL = {AJAX_URL}')
    
    # Create output dir
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Launch browser
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(options=options, version_main=148)
    
    try:
        # Bypass Cloudflare
        print('Bypassing Cloudflare...')
        driver.get(BASE_URL)
        time.sleep(20)
        
        # ===== PHASE 1: Scrape all series from category =====
        print(f'\n{"="*60}')
        print('PHASE 1: Scraping series list')
        print(f'Pages: {args.start} to {args.end or "all"}')
        print(f'{"="*60}')
        
        series_list = scrape_all_series(driver, args.start, args.end)
        
        # Save series list
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(series_list, f, ensure_ascii=False, indent=2)
        print(f'Saved series list: {args.output}')
        
        if args.series_only:
            print('Series-only mode. Skipping episode scraping.')
            driver.quit()
            sys.exit(0)
        
        # ===== PHASE 2: Fetch episodes & servers for each series =====
        print(f'\n{"="*60}')
        print(f'PHASE 2: Scraping episodes & servers')
        s_start = max(0, args.series_start - 1)
        s_end = args.series_end if args.series_end else len(series_list)
        to_process = series_list[s_start:s_end]
        print(f'Series {args.series_start} to {args.series_end or len(series_list)} ({len(to_process)} of {len(series_list)} total)')
        print(f'{"="*60}')
        
        episode_data = scrape_episodes_for_series(
            driver, to_process, args.output,
            resume=args.resume
        )
        
        print(f'\nSaved detailed data: {args.output}')
        
        # ===== PHASE 3: Convert to standard format =====
        print(f'\n{"="*60}')
        print('PHASE 3: Converting to standard format')
        print(f'{"="*60}')
        
        formatted = convert_to_standard_format(episode_data)
        with open(args.format, 'w', encoding='utf-8') as f:
            json.dump(formatted, f, ensure_ascii=False, indent=2)
        
        # Stats
        total_eps = sum(len(s['episodes']) for s in episode_data)
        total_with_sv = sum(s['episodesWithServers'] for s in episode_data)
        total_links = sum(len(e['servers']) for s in formatted for se in s['seasons'] for e in se['episodes'])
        
        print(f'Series: {len(formatted)}')
        print(f'Episodes: {total_eps}')
        print(f'Episodes with servers: {total_with_sv}')
        print(f'Total server links: {total_links}')
        print(f'Output: {args.format}')
        
    finally:
        try: driver.quit()
        except: pass
