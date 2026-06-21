import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Try IMDB suggest API
try:
    r = requests.get(
        'https://www.imdb.com/auto/suggest/en-us/Inception',
        headers=headers,
        timeout=10
    )
    print('Suggest API Status:', r.status_code)
    print('Response:', r.text[:500])
except Exception as e:
    print('Suggest API error:', e)

# Try the search API with a different approach
print('\n---')

# Try using the OMDb API with their demo key
try:
    r = requests.get(
        'http://www.omdbapi.com/?t=Inception&y=2010&apikey=PlzProvideYourKey',
        timeout=10
    )
    print('OMDb API Status:', r.status_code)
    print('Response:', r.text[:300])
except Exception as e:
    print('OMDb API error:', e)
