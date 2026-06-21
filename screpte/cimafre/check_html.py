import re
t = open('screpte/cimafre/data/detail.html', 'r', encoding='utf-8').read()

# Check for embed URL patterns
for p in ['data-embed-url', 'data-embed', 'embed-url', 'embedurl', 'data-video']:
    found = re.findall(p + r'="([^"]+)"', t)
    if found:
        print(f'{p}: {len(found)}')
        for u in found[:3]: print(f'  {u}')

# Check for download URL patterns
for p in ['data-download-url', 'data-download', 'download-url', 'downloadurl']:
    found = re.findall(p + r'="([^"]+)"', t)
    if found:
        print(f'{p}: {len(found)}')
        for u in found[:3]: print(f'  {u}')

# Check for WatchList section
idx = t.find('WatchList')
if idx >= 0:
    section = t[idx:idx+2000]
    print(f'\nWatchList section:')
    print(section[:1000])

# Check for تحميل section
idx = t.find('تحميل')
if idx >= 0:
    section = t[idx:idx+2000]
    print(f'\nDownload section:')
    print(section[:1000])
