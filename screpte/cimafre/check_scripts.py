import re
t = open('screpte/cimafre/data/detail.html', 'r', encoding='utf-8').read()

# Find all script tags
scripts = re.findall(r'<script[^>]*src="([^"]+)"', t)
print(f'External scripts: {len(scripts)}')
for s in scripts:
    print(f'  {s}')

# Find inline scripts that reference AJAX or API
inline = re.findall(r'<script[^>]*>(.*?)</script>', t, re.DOTALL)
print(f'\nInline scripts: {len(inline)}')
for i, s in enumerate(inline):
    if 'ajax' in s.lower() or 'fetch' in s.lower() or 'getJSON' in s or '$.get' in s or '$.post' in s or 'load_' in s or 'embed' in s.lower():
        print(f'\nInline script {i}:')
        print(s[:500])
