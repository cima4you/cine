import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

urls = [
    'https://media0101.elcinema.com/uploads/_315x420_8d3cb112dfa7f23ee82f3deab6f33957705ed9b920813e86ee2bc3a10e109bc8.jpg',
    'https://media0101.elcinema.com/uploads/_810x1080_8d3cb112dfa7f23ee82f3deab6f33957705ed9b920813e86ee2bc3a10e109bc8.jpg',
]

for url in urls:
    # Without referer
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(f'No referer: {url.split("/")[-2][:8]} -> {r.status_code} {len(r.content)}')
    
    # With elcinema referer
    r2 = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.elcinema.com/'})
    print(f'With referer: {url.split("/")[-2][:8]} -> {r2.status_code} {len(r2.content)}')
    
    # With work page referer
    r3 = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.elcinema.com/work/2098675/'})
    print(f'With work ref: {url.split("/")[-2][:8]} -> {r3.status_code} {len(r3.content)}')
    print()
