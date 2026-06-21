import requests, re

ajax_url = 'https://web.topcinemaa.com/wp-content/themes/movies2023/Ajaxat/Single/Server.php'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
    'X-Requested-With': 'XMLHttpRequest',
}

out = []
post_id = '225459'

# Test each server (0-8)
for i in range(9):
    r = requests.post(ajax_url, headers=headers, data={'id': post_id, 'i': str(i)}, timeout=30)
    r.encoding = 'utf-8'
    data = r.text
    out.append('Server {} ({} chars):'.format(i, len(data)))
    out.append(data[:500])
    
    # Check for iframe
    iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', data)
    if iframes:
        out.append('  Iframe: {}'.format(iframes[0]))
    
    # Check for data-src
    data_src = re.findall(r'data-src="([^"]+)"', data)
    if data_src:
        out.append('  data-src: {}'.format(data_src[0]))
    
    # Check for any URL
    urls = re.findall(r'(https?://[^"\'\s<>]+)', data)
    for u in urls:
        out.append('  URL: {}'.format(u[:100]))

with open('D:\\Users\\DT01\\Desktop\\rachid-site\\scripts\\topcinema\\debug_ajax_servers.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Done')
