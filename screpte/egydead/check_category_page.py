import cloudscraper, re
scraper = cloudscraper.create_scraper()
headers = {'User-Agent': 'Mozilla/5.0'}

# Try the category page
url = 'https://tv8.egydead.live/category/english-movies/'
r = scraper.get(url, timeout=20, headers=headers)
html = r.text
print('URL:', r.url)
print('Status:', r.status_code)
print('Length:', len(html))

if 'Just a moment' in html:
    print("BLOCKED by Cloudflare")
else:
    # Check what HTML structure the items have
    items = re.findall(r'<li class="movieItem">(.*?)</li>', html, re.DOTALL)
    print('Items found:', len(items))
    if items:
        print('\nFirst item:')
        print(items[0][:500])
    
    # Also check for alternative patterns
    for pat in [r'class="[^"]*post[^"]*"', r'class="[^"]*movie[^"]*"', r'class="[^"]*item[^"]*"', r'<article']:
        m = re.findall(pat, html)
        if m:
            print('\nPattern {}: {} matches'.format(pat, len(m)))
    
    # Show some of the page content to understand structure
    print('\n--- page content (around "movieItem" or "post") ---')
    for keyword in ['movieItem', 'post', 'film', 'فيلم']:
        idx = html.find(keyword)
        if idx >= 0:
            print('Found "{}" at position {}:'.format(keyword, idx))
            print(html[max(0,idx-100):idx+400])
            print()
            break
