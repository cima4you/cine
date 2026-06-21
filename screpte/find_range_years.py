import re, sys

sys.stdout.reconfigure(encoding='utf-8')

for fp in [r'test\data.js', r'RACHID\data.js', r'split\data-foreign.js']:
    path = r'D:\Users\DT01\Desktop\rachid-site' + '\\' + fp
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for val in ['2023-2073', '2039-2073', '-']:
        matches = list(re.finditer(val, content))
        if matches:
            print(f'{fp}: "{val}" found {len(matches)} times')
            for m in matches[:2]:
                ctx = content[max(0,m.start()-100):m.end()+100]
                print(f'  ...{ctx}...')
        else:
            print(f'{fp}: "{val}" not found')
    print()
