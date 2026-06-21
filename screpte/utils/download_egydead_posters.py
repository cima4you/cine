#!/usr/bin/env python3
"""
Download all egydead.live poster images locally to fix Cloudflare cross-origin block.
Uses Playwright to bypass Cloudflare JS challenge.
"""
import json, os, sys, time
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_JS = os.path.join(PROJECT_DIR, 'data.js')
IMG_DIR = os.path.join(PROJECT_DIR, 'posters')
os.makedirs(IMG_DIR, exist_ok=True)

with open(DATA_JS, 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])
prefix = c[:c.index('[')]
suffix = c[c.rindex(']')+1:]

# Find all egydead.live poster URLs
egydead_items = []
for i, item in enumerate(data):
    poster = item.get('poster', '')
    if 'egydead.live' in poster:
        # Generate local filename
        ext = os.path.splitext(poster.split('/')[-1])[1] or '.jpg'
        local_name = 'poster_%d%s' % (i, ext)
        egydead_items.append((i, poster, local_name))

print('Found %d egydead.live posters to download' % len(egydead_items))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('Playwright not installed. Installing...')
    os.system('pip install playwright')
    os.system('playwright install chromium')
    from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        locale='en-US'
    )
    page = context.new_page()
    
    # First visit egydead.live to solve Cloudflare challenge
    print('Visiting egydead.live to solve Cloudflare challenge...')
    try:
        page.goto('https://tv8.egydead.live/', timeout=60000)
        page.wait_for_load_state('networkidle', timeout=60000)
        print('  Page loaded: %s' % page.title())
    except Exception as e:
        print('  Warning: %s' % str(e))
    
    time.sleep(2)
    
    downloaded = 0
    failed = 0
    
    for idx, poster_url, local_name in egydead_items:
        local_path = os.path.join(IMG_DIR, local_name)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
            downloaded += 1
            continue
        
        try:
            response = page.goto(poster_url, timeout=30000, wait_until='domcontentloaded')
            time.sleep(0.5)
            
            # Check if we got an image or a challenge page
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                # Save the image
                img_data = response.body()
                with open(local_path, 'wb') as f:
                    f.write(img_data)
                downloaded += 1
                if downloaded % 10 == 0:
                    print('  Downloaded: %d/%d' % (downloaded, len(egydead_items)))
            else:
                failed += 1
                if failed <= 5:
                    print('  Failed[%d] %s: content-type=%s' % (idx, poster_url[-30:], content_type))
        except Exception as e:
            failed += 1
            if failed <= 5:
                print('  Error[%d]: %s' % (idx, str(e)[:60]))
    
    browser.close()

print('\nDownloaded: %d, Failed: %d out of %d' % (downloaded, failed, len(egydead_items)))

if downloaded > 0:
    # Update data.js with local paths
    for idx, poster_url, local_name in egydead_items:
        local_path = os.path.join(IMG_DIR, local_name)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
            data[idx]['poster'] = 'posters/' + local_name
    
    json_str = json.dumps(data, ensure_ascii=False)
    with open(DATA_JS, 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)
    print('data.js updated with local poster paths')
