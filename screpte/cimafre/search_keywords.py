import re
t = open('screpte/cimafre/data/detail.html', 'r', encoding='utf-8').read()

# Search for any occurrence of embed in any form
for keyword in ['embed', 'Cimaf', 'vk.com', 'vidspeed', 'larhu', 'uqload', 'WatchList']:
    idx = t.find(keyword)
    if idx >= 0:
        print(f'Found "{keyword}" at pos {idx}')
        print(t[max(0,idx-100):idx+200])
        print('---')
    else:
        print(f'NOT found: "{keyword}"')
