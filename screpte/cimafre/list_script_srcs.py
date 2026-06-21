import re
t = open('screpte/cimafre/data/detail.html', 'r', encoding='utf-8').read()
srcs = re.findall(r'<script[^>]*src="([^"]+)"', t)
print(f'All script srcs ({len(srcs)}):')
for s in srcs:
    print(f'  {s}')
