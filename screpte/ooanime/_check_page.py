import re, json

with open('page.html', 'r', encoding='utf-8') as f:
    t = f.read()

results = {}
results['page_length'] = len(t)
m = re.search(r'<title>(.*?)</title>', t, re.DOTALL)
results['title'] = m.group(1).strip() if m else 'NONE'

# Find all links
links = re.findall(r'href="([^"]+)"', t)
results['cartoon_links'] = [l for l in links if 'cartoon' in l.lower()][:10]
results['series_links'] = [l for l in links if 'series' in l.lower()][:10]
results['episode_links'] = [l for l in links if 'episode' in l.lower()][:10]

# Pagination
pages = re.findall(r'\?page=(\d+)', t)
results['pages'] = pages[:20]

# Cards / content overlays
cards = re.findall(r'href="(/series/\d+/[^"]+)"', t)
results['series_hrefs'] = cards[:20]
print(json.dumps(results, ensure_ascii=False, indent=2))
