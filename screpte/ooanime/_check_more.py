import requests, re, json

base = 'https://www.ooanime.com'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

results = {}

# Test various page patterns
patterns = [
    '/cartoon',
    '/cartoon?page=2',
    '/cartoon?page=3',
    '/cartoon?start=36',
    '/cartoon?offset=36',
    '/cartoon?limit=36&offset=36',
    '/cartoon/2',
    '/cartoon/page/2',
]

for p in patterns:
    try:
        r = requests.get(base + p, headers=headers, timeout=10)
        r.encoding = 'utf-8'
        series = len(re.findall(r'/series/(\d+)/', r.text))
        results[p] = f'{series} series, {len(r.text)} bytes'
    except Exception as e:
        results[p] = str(e)

# Also check the /tvseries endpoint (different category)
r = requests.get(base + '/tvseries', headers=headers, timeout=10)
r.encoding = 'utf-8'
series = len(re.findall(r'/series/(\d+)/', r.text))
results['/tvseries'] = f'{series} series, {len(r.text)} bytes'

# Check for search with empty query
r = requests.get(base + '/search_series?q=', headers=headers, timeout=10)
r.encoding = 'utf-8'
series = len(re.findall(r'/series/(\d+)/', r.text))
results['/search_series?q='] = f'{series} series, {len(r.text)} bytes'

# Check for any load more AJAX endpoint
r = requests.get(base + '/cartoon', headers=headers, timeout=10)
r.encoding = 'utf-8'
# Look for data attributes or JS that loads more
data_atts = re.findall(r'data-[^=]+="([^"]*load[^"]*)"', r.text, re.IGNORECASE)
results['data_load_attributes'] = data_atts[:5]

# Check if there's a different page source
ajax_eps = re.findall(r'(getMore|loadData|fetchData|pageContent|seriesList)', r.text)
results['ajax_function_names'] = ajax_eps[:10]

# Check the total series count mentioned anywhere
counts = re.findall(r'(\d+)\s*(?:series|series|مسلسل|cartoon|كرتون)', r.text, re.IGNORECASE)
results['count_mentions'] = counts[:5]

# Check for any hidden inputs
hidden = re.findall(r'<input[^>]*type="hidden"[^>]*value="(\d+)"', r.text)
results['hidden_values'] = hidden[:5]

print(json.dumps(results, ensure_ascii=False, indent=2))
