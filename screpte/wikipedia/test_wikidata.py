import requests
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Test Wikidata query for IMDB ID
wikidata_id = 'Q137917335'
url = f'https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json'
r = requests.get(url, headers=headers, timeout=10)
data = r.json()
entity = data.get('entities', {}).get(wikidata_id, {})
claims = entity.get('claims', {})
# P345 is the IMDB ID property
imdb_claim = claims.get('P345', [])
if imdb_claim:
    imdb_id = imdb_claim[0].get('mainsnak', {}).get('datavalue', {}).get('value', '')
    print('IMDB ID:', imdb_id)
else:
    print('No IMDB ID in Wikidata')
    # Show available properties
    available = list(claims.keys())
    print('Available properties:', available[:10])
