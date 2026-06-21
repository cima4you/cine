import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

# Find all unique image domains in posters
domains = {}
for item in data:
    p = item.get('poster', '')
    m = re.search(r'https?://([^/]+)', p)
    if m:
        domain = m.group(1)
        domains[domain] = domains.get(domain, 0) + 1

print('Poster domains:')
for d, cnt in sorted(domains.items(), key=lambda x: -x[1]):
    print('  %s: %d' % (d, cnt))

# Check specifically for egydead-related domains
print('\nAny egydead domains:')
for d, cnt in sorted(domains.items(), key=lambda x: -x[1]):
    if 'egydead' in d.lower():
        print('  %s: %d' % (d, cnt))
