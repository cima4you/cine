import requests, re

headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a/page/2/'
r = requests.get(url, headers=headers, timeout=15)

# Find "item" blocks
items = re.findall(r'<li[^>]*class="[^"]*item[^"]*"[^>]*>(.*?)</li>', r.text, re.DOTALL)
print('Item blocks: {}'.format(len(items)))

# Check each item block for movie content
movie_count = 0
for item in items:
    a = re.search(r'href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]*)"', item)
    img = re.search(r'<img[^>]*alt="([^"]+)"', item)
    if a and img:
        movie_count += 1
        
print('Movie items (with href+img): {}'.format(movie_count))

# Show first few non-movie items
non_movie = 0
for item in items:
    a = re.search(r'href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]*)"', item)
    if not a:
        non_movie += 1
        if non_movie <= 3:
            print('\nNon-movie item content:')
            print(item[:200])
