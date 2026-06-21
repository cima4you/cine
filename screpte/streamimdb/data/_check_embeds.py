import requests, re, json

# Check a listing page for embed IDs
r = requests.get('https://streamimdb.ru/movies?vaplayer_path=movies&page=1',
  headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
r.encoding = 'utf-8'

results = {}

# Look for data-src on the listing page
ds = re.findall(r'data-src="(/embed/movie/\d+)"', r.text)
results['data_src_on_listing'] = ds[:5]

# Look for numeric IDs anywhere
nums = re.findall(r'/embed/movie/(\d+)', r.text)
results['embed_ids_on_listing'] = nums[:5]

# Look for the pattern in cards
cards = re.findall(r'<div class="cb-card".*?</div>', r.text, re.DOTALL)
results['total_cards'] = len(cards)

# Check if any card has the embed info
for i, card in enumerate(cards[:3]):
    has_embed = '/embed/movie/' in card
    has_data_src = 'data-src' in card
    results[f'card_{i}_has_embed'] = has_embed
    results[f'card_{i}_has_data_src'] = has_data_src

# Also check other embed patterns on page
all_patterns = [
    r'data-src="([^"]*)"',
    r'/embed/movie/(\d+)',
    r'nextgencloudfabric',
]
for pat in all_patterns:
    matches = re.findall(pat, r.text)
    results[f'pattern_{pat[:30]}'] = matches[:5]

with open('screpte/streamimdb/data/_embed_check.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('Saved to _embed_check.json')
