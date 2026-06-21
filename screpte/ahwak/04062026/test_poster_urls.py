import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/ahwak/data/results_ahwak_moslslat_ramdan_2022.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

titles = ['توبة', 'ظل', 'سكة سفر', 'منعطف خطر', 'يوتيرن', 'ازمة منتصف العمر', 'عاصفة']

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

print('=== Without Referer ===')
for t in titles:
    found = [x for x in data if x['title'].strip() == t]
    if found:
        url = found[0]['poster']
        try:
            r = s.head(url, timeout=10, allow_redirects=True)
            print('%s: %d (%d bytes)' % (t, r.status_code, int(r.headers.get('content-length', 0))))
        except Exception as e:
            print('%s: ERROR %s' % (t, e))

print('\n=== With elcinema Referer ===')
s.headers.update({'Referer': 'https://www.elcinema.com/'})
for t in titles:
    found = [x for x in data if x['title'].strip() == t]
    if found:
        url = found[0]['poster']
        try:
            r = s.head(url, timeout=10, allow_redirects=True)
            print('%s: %d (%d bytes)' % (t, r.status_code, int(r.headers.get('content-length', 0))))
        except Exception as e:
            print('%s: ERROR %s' % (t, e))

# Also try full GET on one
print('\n=== Full GET on توبة ===')
r = s.get(found[0]['poster'], timeout=10, stream=True)
print('Status: %d' % r.status_code)
print('Headers: %s' % dict(r.headers))
print('Content (first 200 bytes): %s' % r.content[:200])
