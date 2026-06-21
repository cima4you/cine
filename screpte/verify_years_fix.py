import re, sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

files = [
    r'D:\Users\DT01\Desktop\rachid-site\test\data.js',
    r'D:\Users\DT01\Desktop\rachid-site\RACHID\data.js',
    r'D:\Users\DT01\Desktop\rachid-site\split\data-foreign.js',
]

for fp in files:
    name = fp.split('\\')[-1]
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_years = [m.group(1) for m in re.finditer(r'"year":\s*"(\d*)"', content)]
    c = Counter(all_years)
    
    invalid = {y: v for y, v in c.items() if y and not (1888 <= int(y) <= 2026)}
    
    print(f'{name}:')
    print(f'  Total year fields: {sum(c.values())}')
    print(f'  Empty years: {c.get("", 0)}')
    print(f'  Invalid years: {sum(invalid.values())}')
    if invalid:
        for y in sorted(invalid):
            print(f'    {y}: {invalid[y]}')
    else:
        print(f'  ✅ All years valid (1888-2026)')
    print()
