from curl_cffi import requests as curl_requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

# Try different impersonate options
options = ['chrome124', 'chrome123', 'chrome120', 'chrome110', 'chrome101', 'safari17_0', 'safari16_5', 'firefox124', 'firefox123', 'firefox120']

for imp in options:
    try:
        r = curl_requests.get('https://tv8.egydead.live/', impersonate=imp, headers=headers, timeout=15)
        blocked = 'Just a moment' in r.text or 'challenge' in r.text.lower()[:200]
        print('{}: status={}, len={}, blocked={}'.format(imp, r.status_code, len(r.text), blocked))
        if not blocked and r.status_code == 200:
            import re
            items = re.findall(r'<li class="movieItem">(.*?)</li>', r.text, re.DOTALL)
            print('  ITEMS FOUND:', len(items))
            # Save successful response for analysis
            with open('egydead_homepage.html', 'w', encoding='utf-8') as f:
                f.write(r.text)
            break
    except Exception as e:
        print('{}: error: {}'.format(imp, e))
