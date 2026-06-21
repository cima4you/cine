import requests, re
r = requests.get('https://tuktukhd.com/category/movies-2/', headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
text = r.content.decode('utf-8')

# Find all subcategory links
cats = re.findall(r'<a[^>]*href="(https://tuktukhd\.com/category/movies-2/[^"]*)"[^>]*>([^<]+)</a>', text)
print('Subcategories found: {}'.format(len(cats)))
for url, name in cats:
    print(f'  {name.strip():30s} -> {url[:70]}')
