import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Test Wikipedia API
params = {
    'action': 'query',
    'titles': 'Vadh 2',
    'prop': 'pageprops',
    'format': 'json'
}

r = requests.get('https://en.wikipedia.org/w/api.php', params=params, headers=headers, timeout=10)
print('Status:', r.status_code)
print('Content-Type:', r.headers.get('Content-Type'))
print('Text (first 200):', r.text[:200])

if r.text:
    data = r.json()
    print('Pages:', data.get('query', {}).get('pages', {}))
else:
    print('Empty response')
