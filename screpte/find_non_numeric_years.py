import re, sys

sys.stdout.reconfigure(encoding='utf-8')

# Broader search: find any year field containing a hyphen or non-numeric values
for fp in [r'test\data.js', r'RACHID\data.js', r'split\data-foreign.js']:
    path = r'D:\Users\DT01\Desktop\rachid-site' + '\\' + fp
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find year values that are NOT empty and NOT purely numeric
    bad = []
    for m in re.finditer(r'"year":\s*"([^"]+)"', content):
        val = m.group(1)
        if val and not val.isdigit():
            bad.append(val)
    
    if bad:
        from collections import Counter
        c = Counter(bad)
        print(f'{fp}: {len(bad)} non-numeric year values:')
        for y, cnt in c.most_common():
            print(f'  "{y}" x{cnt}')
    else:
        print(f'{fp}: no non-numeric year values ✅')
    print()
