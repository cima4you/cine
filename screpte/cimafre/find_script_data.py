import re
t = open('screpte/cimafre/data/detail.html', 'r', encoding='utf-8').read()

# Find all script contents
scripts = re.findall(r'<script[^>]*>(.*?)</script>', t, re.DOTALL)
print(f'Scripts: {len(scripts)}')

for i, s in enumerate(scripts):
    s = s.strip()
    if not s:
        continue
    # Look for any object with video/embed URLs
    if 'embed' in s.lower() or 'http' in s or 'source' in s.lower():
        print(f'\n=== Script {i} ({len(s)} chars) ===')
        # Show relevant parts
        for line in s.split('\n'):
            line_s = line.strip()
            if any(kw in line_s.lower() for kw in ['embed', 'http', 'source', 'server', 'video', 'watch', 'stream']):
                print(f'  {line_s[:200]}')
