import re, json

t = open('screpte/cimafre/data/detail.html', 'r', encoding='utf-8').read()

# 1. Find pm_video_data
data_match = re.search(r'var pm_video_data\s*=\s*({.*?});', t, re.DOTALL)
if data_match:
    print('=== pm_video_data ===')
    print(data_match.group(1)[:500])

# 2. Find all script tags with source/embed/servers references
scripts = re.findall(r'<script[^>]*>(.*?)</script>', t, re.DOTALL)
print(f'\n=== Total scripts: {len(scripts)} ===')

for i, s in enumerate(scripts):
    if any(kw in s for kw in ['embed', 'server', 'source', 'video_url', 'WatchList', 'load_stream']):
        print(f'\nScript {i} ({len(s)} chars):')
        for kw in ['embed', 'server', 'source', 'video_url', 'WatchList', 'load_stream']:
            for line in s.split('\n'):
                ls = line.strip()
                if kw in ls:
                    print(f'  {ls[:200]}')

# 3. Check the actual WatchList section in HTML
watchlist_section = re.search(r'<ul[^>]*class="[^"]*WatchList[^"]*"[^>]*>.*?</ul>', t, re.DOTALL)
if watchlist_section:
    print('\n=== WatchList UL found in HTML ===')
    print(watchlist_section.group(0)[:2000])
else:
    print('\n=== WatchList UL NOT found in HTML ===')
    # check for any ul with server-related classes
    ul_sections = re.findall(r'<ul[^>]*class="[^"]*(?:nav|server|list|source)[^"]*"[^>]*>.*?</ul>', t, re.DOTALL)
    print(f'  Other relevant ULs: {len(ul_sections)}')
    for ul in ul_sections[:2]:
        print(f'  {ul[:300]}')

# 4. Look for inline JSON data (maybe server data is embedded as JSON in a script tag)
json_like = re.findall(r'"server_name"\s*:\s*"[^"]*"|"embed_url"\s*:\s*"[^"]*"|server_url.*?:.*?".*?"', t)
if json_like:
    print(f'\n=== JSON-like server data found: {len(json_like)} ===')
    for jl in json_like[:10]:
        print(f'  {jl[:150]}')

# 5. Look for any script with a large JSON object
for i, s in enumerate(scripts):
    s = s.strip()
    if len(s) > 200 and ('{' in s) and ('video' in s or 'source' in s or 'embed' in s):
        if 'pm_video_data' not in s:  # already found
            print(f'\n=== Script {i} (large, {len(s)} chars) ===')
            print(s[:500])
