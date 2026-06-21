import re, json

t = open('page.html','r',encoding='utf-8').read()

nav = re.findall('href="/tvseries\\?category=([^"]+)"', t)
print('Nav links:', len(nav))
for n in nav[:20]:
    print(' ', n)
cats = set(nav)
print('Unique categories:', len(cats))
for c in sorted(cats):
    print(' ', c)

# Also check the main nav items
main_nav = re.findall(r'<a[^>]*href="/([^"]+)"[^>]*>([^<]+)</a>', t)
print('\nMain nav:', len(main_nav))
for href, text in main_nav:
    print(f'  /{href} -> {text.strip()[:30]}')
