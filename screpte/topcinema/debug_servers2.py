import requests, re, json

url = 'https://web.topcinemaa.com/%D9%81%D9%8A%D9%84%D9%85-vampires-of-the-velvet-lounge-2026-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/watch/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}
r = requests.get(url, headers=headers, timeout=30)
r.encoding = 'utf-8'
html = r.text

with open('D:\\Users\\DT01\\Desktop\\rachid-site\\scripts\\topcinema\\debug_watch.html', 'w', encoding='utf-8') as f:
    f.write(html)

out = []

# 1. Find all server--item with data-server attribute
server_items = re.findall(
    r'<li[^>]*data-id="(\d+)"[^>]*data-server="(\d+)"[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>(.*?)</span>',
    html, re.DOTALL
)
out.append('Server items with data-id/server: {}'.format(len(server_items)))
for data_id, data_server, name in server_items:
    out.append('  data-id={}, data-server={}, name={}'.format(data_id, data_server, name.strip()))

# 2. Check all server--item regardless
server_items2 = re.findall(
    r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>(.*?)</li>',
    html, re.DOTALL
)
out.append('\nAll server--item blocks: {}'.format(len(server_items2)))
for si in server_items2[:5]:
    out.append('  {}'.format(si[:200]))

# 3. Check for script tags that might contain server URLs
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
out.append('\nScripts: {}'.format(len(scripts)))
for i, sc in enumerate(scripts):
    if any(kw in sc.lower() for kw in ['server', 'iframe', 'player', 'watch', 'vidtube', 'embed', 'data-crypt']):
        out.append('  Script {} ({} chars):'.format(i, len(sc)))
        out.append('    {}'.format(sc[:800]))
        out.append('    ...')
        if len(sc) > 800:
            out.append('    {}'.format(sc[-500:]))

# 4. Check for data-crypt
data_crypts = re.findall(r'data-crypt="([^"]+)"', html)
out.append('\ndata-crypt values: {}'.format(len(data_crypts)))
for dc in data_crypts[:5]:
    out.append('  {}'.format(dc[:100]))

# 5. Check for data-url
data_urls = re.findall(r'data-url="([^"]+)"', html)
out.append('\ndata-url values: {}'.format(len(data_urls)))
for du in data_urls[:5]:
    out.append('  {}'.format(du[:100]))

# 6. Check for data-lnk
data_lnk = re.findall(r'data-lnk="([^"]+)"', html)
out.append('\ndata-lnk values: {}'.format(len(data_lnk)))
for dl in data_lnk[:5]:
    out.append('  {}'.format(dl[:100]))

# 7. Check watch--area for player content
watch_area = re.search(r'<div class="watch--area[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
if watch_area:
    out.append('\nWatch area ({} chars):'.format(len(watch_area.group(1))))
    out.append(watch_area.group(1)[:1500])

# 8. Find any object/embed/param tags
objects = re.findall(r'<(object|embed|param|video|source)[^>]*>', html)
out.append('\nMedia tags: {}'.format(len(objects)))
for o in objects:
    out.append('  {}'.format(o[:200]))

with open('D:\\Users\\DT01\\Desktop\\rachid-site\\scripts\\topcinema\\debug_watch_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Done')
