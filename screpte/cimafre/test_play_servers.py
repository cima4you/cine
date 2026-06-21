import requests, re, json

headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ar,en'}
s = requests.Session()
s.get('https://cimafre.site/', timeout=20)

vids = ['19997b01f', '09f9f582b', '7055ee7e7']

for vid in vids:
    r = s.get(f'https://cimafre.site/play.php?vid={vid}', headers=headers, timeout=20)
    r.encoding = 'utf-8'
    t = r.text
    
    servers = re.findall(
        r'<li[^>]*data-embed-id="(\d+)"[^>]*data-embed-url="([^"]+)"[^>]*>.*?<strong>(.*?)</strong>',
        t, re.DOTALL
    )
    
    print(f'\n{vid}: {len(servers)} servers')
    for sid, url, name in servers:
        print(f'  [{sid}] {name.strip()}: {url}')
    
    # Also extract DownloadList
    downloads = re.findall(
        r'<li[^>]*data-download-url="([^"]+)"[^>]*>.*?<strong>(.*?)</strong>',
        t, re.DOTALL
    )
    if downloads:
        print(f'  Downloads:')
        for url, name in downloads:
            print(f'    {name.strip()}: {url}')
