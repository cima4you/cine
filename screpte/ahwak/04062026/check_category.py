import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://yam.ahwaktv.net'
for cat in ['moslslat-ramdan-2022', 'moslslat-ramadan-2023', 'moslslat-ramadan-2024']:
    url = BASE + '/category.php?cat=' + cat
    print('=== %s ===' % url)
    r = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }, verify=False, timeout=30)
    print('Status:', r.status_code)
    print('Length:', len(r.text))
    # Check page count
    pages = re.findall(r'\?page=(\d+)', r.text)
    print('Pages found:', pages)
    if pages:
        print('Max page:', max(int(p) for p in pages))
    # Check how many watch.php links
    vids = re.findall(r'watch\.php\?vid=([a-f0-9]+)', r.text)
    print('Vids on first page:', len(vids))
    # Check if category exists
    if 'لم يتم العثور' in r.text or 'No results' in r.text or '404' in r.text[:500]:
        print('WARNING: Empty/no results')
    # Print title
    m = re.search(r'<title>([^<]*)</title>', r.text)
    if m:
        print('Title:', m.group(1))
    print()
