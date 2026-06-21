import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

metropolis = [item for item in data if 'metropolis' in item.get('title','').lower()]
print('Metropolis entries:', len(metropolis))
for item in metropolis:
    print('  title:', item.get('title'))
    print('  year:', item.get('year'))
    print('  type:', item.get('type'))
    print()

# Check all years
years = {}
for item in data:
    y = item.get('year','')
    if y:
        years[y] = years.get(y, 0) + 1

print('All years and counts:')
for y in sorted(years.keys(), key=lambda x: int(x) if x.isdigit() else 9999):
    print('  %s: %d items' % (y, years[y]))
