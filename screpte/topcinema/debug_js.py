import requests, re, json

# Check main movie page for JavaScript that loads servers
main_url = 'https://web.topcinemaa.com/%D9%81%D9%8A%D9%84%D9%85-vampires-of-the-velvet-lounge-2026-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}
r = requests.get(main_url, headers=headers, timeout=30)
r.encoding = 'utf-8'
html = r.text

out = []

# Find all script src
script_srcs = re.findall(r'<script[^>]*src="([^"]+)"', html)
out.append('External scripts: {}'.format(len(script_srcs)))
for s in script_srcs:
    out.append('  {}'.format(s))

# Find inline scripts that mention server or ajax
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
out.append('\nInline scripts: {}'.format(len(scripts)))
for i, sc in enumerate(scripts):
    if any(kw in sc.lower() for kw in ['server', 'ajax', 'embed', 'player', 'iframe', 'vidtube', 'data-id']):
        out.append('  Script {} ({} chars):'.format(i, len(sc)))
        out.append('    {}'.format(sc[:2000]))
        if len(sc) > 2000:
            out.append('    ...(truncated)')

# Check for any wp-ajax or admin-ajax
ajax_urls = re.findall(r'admin-ajax\.php|wp-ajax|rest-route|wp-json', html)
out.append('\nAJAX endpoints found: {}'.format(len(ajax_urls)))
for a in ajax_urls:
    out.append('  {}'.format(a))

# Search for any URL pattern with the post ID (225459)
post_id_patterns = re.findall(r'225459', html)
out.append('\nPost ID 225459 mentions: {}'.format(len(post_id_patterns)))

# Search for vidtube in scripts
for i, sc in enumerate(scripts):
    if 'vidtube' in sc.lower() or 'embed' in sc.lower():
        out.append('\nScript {} with vidtube/embed:'.format(i))
        out.append(sc[:2000])

with open('D:\\Users\\DT01\\Desktop\\rachid-site\\scripts\\topcinema\\debug_js_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Done')
