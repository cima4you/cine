import requests, re, json, base64

headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-cuckoo-2024-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'
r = requests.get(url, timeout=15, headers=headers)

# Find server list items (li with data-link and server--item class)
server_items = re.findall(r'<li[^>]*data-link="([^"]*)"[^>]*class="[^"]*server--item[^"]*"[^>]*>', r.text)
print('Server links found:', len(server_items))

# Better: find entire server items with both data-link and span
items = re.findall(r'<li[^>]*data-link="([^"]*)"[^>]*class="([^"]*)"[^>]*>(.*?)</li>', r.text, re.DOTALL)
print('Full server items found:', len(items))
for data_link, cls, content in items:
    name = re.search(r'<span>([^<]*)</span>', content)
    name_text = name.group(1).strip() if name else '(no span)'
    print('  name="{}" class="{}" data_link="{}"'.format(name_text, cls, data_link[:50]))

# Also check for data-crypt (these should be in the page)
crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
print('\ndata-crypt values:', len(crypts))
for c in crypts:
    try:
        decoded = base64.b64decode(c).decode('utf-8')
        print('  {}'.format(decoded))
    except:
        pass

# Check download links
dls = re.findall(r'data-real-url="([^"]+)"', r.text)
print('\nDownload links:', len(dls))
for d in dls:
    print('  {}'.format(d))
