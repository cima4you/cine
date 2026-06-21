import requests, re
headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ar,en'}
s = requests.Session()
s.get('https://cimafre.site/', headers=headers, timeout=20)
r = s.get('https://cimafre.site/play.php?vid=19997b01f', headers=headers, timeout=20)
r.encoding = 'utf-8'
t = r.text
m = re.search(r'<ul[^>]*class="[^"]*WatchList[^"]*"[^>]*>.*?</ul>', t, re.DOTALL)
if m:
    print('WatchList IN play.php!')
    print(m.group(0)[:500])
else:
    print('No WatchList in play.php')
    print(f'WatchList count: {t.count("WatchList")}')
