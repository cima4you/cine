import json, os, re, sys, base64
sys.stdout.reconfigure(encoding='utf-8')

INPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data_egydead_series.json')
INPUT = os.path.normpath(INPUT)

BASE = 'https://tv8.egydead.live'

def b64_decode(s):
    s += '=' * (4 - len(s) % 4)
    return base64.b64decode(s).decode('utf-8')

def decode_url(url):
    if not url:
        return url
    if url.startswith('//'):
        return 'https:' + url
    m = re.match(r'(?:https?://tv8\.egydead\.live)?/play\.php\?url=([A-Za-z0-9+/=]+)', url)
    if m:
        try:
            return b64_decode(m.group(1))
        except:
            pass
    m = re.match(r'(?:https?://tv8\.egydead\.live)?/play/\?id=([A-Za-z0-9+/=]+)', url)
    if m:
        try:
            return b64_decode(m.group(1))
        except:
            pass
    if url.startswith('/') and not url.startswith('//'):
        return BASE + url
    return url

if not os.path.exists(INPUT):
    print(f'File not found: {INPUT}')
    sys.exit(1)

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

fixed = 0
for item in data:
    for sv in item.get('servers', []):
        orig = sv['url']
        new = decode_url(orig)
        if new != orig:
            sv['url'] = new
            fixed += 1

with open(INPUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Fixed {fixed} URLs in {len(data)} series')
