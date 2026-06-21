import re
t = open('screpte/cimafre/data/detail.html', 'r', encoding='utf-8').read()

# Find all data-embed-url occurrences
all_embed = [(m.start(), m.group()) for m in re.finditer(r'data-embed-url[= ]', t)]
print(f'data-embed-url occurrences: {len(all_embed)}')
for pos, text in all_embed[:3]:
    print(f'  pos {pos}: {t[pos:pos+100]}')

# Find all data-download-url
all_dl = [(m.start(), m.group()) for m in re.finditer(r'data-download-url[= ]', t)]
print(f'data-download-url occurrences: {len(all_dl)}')
for pos, text in all_dl[:3]:
    print(f'  pos {pos}: {t[pos:pos+100]}')

# Search for li elements around the video player section
# Find the actual movie embed list
idx = t.find('<ul')
while idx >= 0:
    section = t[idx:idx+300]
    if 'WatchList' in section or 'embed' in section or 'download' in section.lower():
        print(f'\nUL at {idx}: {section[:200]}')
        if 'embed-url' in section:
            break
    idx = t.find('<ul', idx+1)
    if idx < 0 or idx > 500000:
        break
