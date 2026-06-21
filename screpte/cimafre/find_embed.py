import re
t = open('screpte/cimafre/data/detail.html', 'r', encoding='utf-8').read()

# Find the one data-embed-url
idx = t.find('data-embed-url')
if idx >= 0:
    print(f'Found at {idx}')
    print(t[idx:idx+200])

# Find WatchList section
idx = t.find('WatchList')
if idx >= 0:
    print(f'\nWatchList 1 at {idx}:')
    print(t[idx-200:idx+400])

idx2 = t.find('WatchList', idx+1)
if idx2 >= 0:
    print(f'\nWatchList 2 at {idx2}:')
    print(t[idx2-200:idx2+400])

# Check what the WatchList li click handler references
js_idx = t.find('WatchList li')
if js_idx >= 0:
    print(f'\nWatchList JS at {js_idx}:')
    print(t[js_idx:js_idx+500])
