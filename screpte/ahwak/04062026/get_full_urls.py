import requests, re, sys, time
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.5'})
s.get('https://www.elcinema.com/')

work_ids = {
    'توبة': '2072893',
    'ظل': '2073216',
    'سكة سفر': '2073681',
    'منعطف خطر': '2074509',
    'يوتيرن': '2072354',
    'ازمة منتصف العمر': '2075848',
    'عاصفة': '2073572',
}

corrections = {}
for title, wid in work_ids.items():
    r = s.get('https://www.elcinema.com/work/%s/' % wid, timeout=15)
    poster = None
    for m in re.finditer(r'<img[^>]*src="([^"]*)"', r.text):
        src = m.group(1)
        if '_315x420' in src and 'uploads' in src:
            poster = src
            break
    print('%s: %s' % (title, poster if poster else 'NOT FOUND'))
    if poster:
        corrections[title] = poster
    time.sleep(0.5)

import json
print('\n--- Python dict ---')
print(json.dumps(corrections, ensure_ascii=False, indent=2))
