import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
entities = re.findall(r'&#(\d+);', c)
print('Remaining HTML entities:', len(entities))
if entities:
    for e in set(entities):
        print('  &#%s;' % e)
idx = c.find("It's Alive")
print("It's Alive found at:", idx)
print('Has &#8217;:', '&#8217;' in c)
# Show the title around that area
if idx >= 0:
    start = max(0, idx - 10)
    end = min(len(c), idx + 30)
    print('Context:', repr(c[start:end]))
