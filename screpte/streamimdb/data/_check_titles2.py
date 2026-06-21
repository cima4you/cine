import requests, re

r = requests.get('https://streamimdb.ru/movies?vaplayer_path=movies&page=1',
  headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
r.encoding = 'utf-8'

# Print raw HTML around first card
cards = re.findall(r'<div class="cb-card".*?</div>', r.text, re.DOTALL)
for i, card in enumerate(cards[:2]):
    print(f'=== CARD {i} ===')
    print(card[:600])
    print('...')
    print()

# Search for any Arabic characters in the entire page
arabic = re.findall(r'[\u0600-\u06FF\u0750-\u077F]{2,}', r.text)
print(f'Arabic phrases found: {len(arabic)}')
for a in arabic[:20]:
    print(f'  {a}')
