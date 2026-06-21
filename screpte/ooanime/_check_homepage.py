import re, json

t = open('series_page.html', 'r', encoding='utf-8').read()

# Find all HomePage sections
homepages = re.findall(r'<div id="HomePage"[^>]*>(.*?)</div>\s*(?:<div class="clr"></div>\s*)?</div>\s*</div>', t, re.DOTALL)
print(f'HomePage divs (flexible): {len(homepages)}')

for i, hp in enumerate(homepages):
    print(f'\nHomePage {i}:')
    print(f'  Length: {len(hp)}')
    print(f'  First 300: {repr(hp[:300])}')
    print(f'  Last 300: {repr(hp[-300:])}')

# Also try simpler pattern - find all divs containing episode-related content
all_divs = re.findall(r'<div[^>]*>(.*?)</div>', t, re.DOTALL)
ep_divs = [d for d in all_divs if 'season' in d.lower() or 'episode' in d.lower() or 'حلقة' in d or 'season' in d]
print(f'\nDivs with season/episode: {len(ep_divs)}')
for d in ep_divs[:5]:
    print(f'  {repr(d[:200])}')

# Search for الحلقة (episode in Arabic)
ar_ep = re.findall(r'الحلقة\s*\d+', t)
print(f'\nArabic episode mentions: {len(ar_ep)}')
print(f'  {ar_ep[:10]}')

# Check for any season/episode related text
all_text = re.findall(r'>([^<]{5,200})<', t)
ep_text = [txt for txt in all_text if any(w in txt.lower() for w in ['season','episode','حلقة','موسم'])]
print(f'\nText containing season/episode: {len(ep_text)}')
for txt in ep_text[:10]:
    print(f'  {repr(txt.strip()[:100])}')
