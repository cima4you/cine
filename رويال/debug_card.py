import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests
BASE = 'https://w9.royal-drama.com'
HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
       'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3'}
r = requests.get(f'{BASE}/category3.php?cat=musalsalat-asiawia&page=1&order=DESC', headers=HDR, timeout=30)
html = r.text
# Find all cards
cards = re.findall(r'<li class="col-xs-6 col-sm-4 col-md-3">(.*?)</li>', html, re.DOTALL)
print(f'Cards found: {len(cards)}')
if cards:
    print('\n=== FIRST CARD ===')
    print(cards[0][:1500])
    print('\n=== SECOND CARD ===')
    print(cards[1][:1500])
