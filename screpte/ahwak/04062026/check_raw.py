import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
idx = c.find("It&#8217;s Alive")
if idx >= 0:
    start = max(0, idx - 200)
    end = min(len(c), idx + 300)
    print('Context:')
    print(c[start:end])
    print()
    print('Has year 8217 in context:', '8217' in c[start:end])
else:
    print('Not found in file')
    # Try without entity
    idx2 = c.find("It's Alive")
    if idx2 >= 0:
        print('Found without entity at', idx2)
