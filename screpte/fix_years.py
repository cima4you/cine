#!/usr/bin/env python3
"""Fix invalid year values in data.js files. Sets out-of-range years to empty string."""
import re, os, sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = r'D:\Users\DT01\Desktop\rachid-site'
FILES = [
    os.path.join(BASE, r'test\data.js'),
    os.path.join(BASE, r'RACHID\data.js'),
    os.path.join(BASE, r'split\data-foreign.js'),
]

def fix_years(text):
    """Replace invalid year values with empty string."""
    def validate_year(m):
        val = m.group(1)
        if not val:
            return m.group(0)
        try:
            y = int(val)
            if 1888 <= y <= 2026:
                return m.group(0)
        except ValueError:
            pass
        return f'"year": ""'

    new_text, count = re.subn(r'"year":\s*"(\d*)"', validate_year, text)
    return new_text, count

for fp in FILES:
    if not os.path.exists(fp):
        print(f'❌ {os.path.basename(fp)}: not found')
        continue
    
    with open(fp, 'r', encoding='utf-8') as f:
        text = f.read()
    
    new_text, count = fix_years(text)
    
    if count > 0:
        tmp = fp + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(new_text)
        os.replace(tmp, fp)
        print(f'✅ {os.path.basename(fp)}: fixed {count} invalid years')
    else:
        print(f'ℹ️ {os.path.basename(fp)}: no changes needed')
