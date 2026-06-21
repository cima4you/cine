import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3'})
s.get('https://yam.ahwaktv.net/', timeout=30)

resp = s.get('https://yam.ahwaktv.net/category.php?cat=moslslat-ramdan-2023', timeout=30)
# Find all page links
page_nums = set()
for m in re.finditer(r'href="[^"]*page=(\d+)"', resp.text):
    page_nums.add(int(m.group(1)))
print('Page numbers found on page 1: %s' % sorted(page_nums))
print('Max page: %d' % max(page_nums))
