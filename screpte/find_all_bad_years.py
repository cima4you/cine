import re, sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

for fp in [r'test\data.js', r'RACHID\data.js', r'split\data-foreign.js']:
    path = r'D:\Users\DT01\Desktop\rachid-site' + '\\' + fp
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find ALL year values (including non-numeric)
    years = []
    for m in re.finditer(r'"year":\s*"([^"]*)"', content):
        years.append(m.group(1))
    
    c = Counter(years)
    
    print(f'{fp}:')
    print(f'  Total years found: {sum(c.values())}')
    
    # Show ALL unique values sorted
    for y in sorted(c.keys()):
        cnt = c[y]
        if not y:
            continue  # skip empty
        if y.isdigit() and 1888 <= int(y) <= 2026:
            continue  # skip valid
        print(f'  ⚠️  "{y}" x{cnt}')
    
    print()
