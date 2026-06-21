#!/usr/bin/env python3
"""إصلاح الأقواس غير المتوازنة - تعيد بناء الملفات من العناصر السليمة فقط"""
import re, os, sys, json

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\Users\DT01\Desktop\rachid-site'
FILES = [
    os.path.join(BASE, r'test\data.js'),
    os.path.join(BASE, r'RACHID\data.js'),
    os.path.join(BASE, r'split\data-foreign.js'),
]

def extract_items(content):
    """Split array content into individual items using brace depth tracking."""
    items = []
    depth = 0
    item_start = None
    in_string = False
    escape = False
    
    for i, ch in enumerate(content):
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        
        if ch == '{':
            if depth == 0:
                item_start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and item_start is not None:
                items.append(content[item_start:i+1])
                item_start = None
        elif ch == ',' and depth == 0:
            continue
    
    return items

def validate_item(item_text):
    """Check if an item has balanced braces and valid JSON."""
    ob = item_text.count('{')
    cb = item_text.count('}')
    if ob != cb:
        return False, f'Braces: {ob} vs {cb}'
    try:
        json.loads(item_text)
        return True, None
    except json.JSONDecodeError as e:
        return False, str(e)

def fix_file(path):
    print(f'\n📂 {os.path.basename(path)}')
    
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Find array
    m = re.search(r'(const\s+\w+\s*=\s*)\[', text)
    if not m:
        print('  ❌ Cannot find array')
        return False
    
    decl_start = m.start()
    arr_start = m.end()
    
    # Find matching closing bracket
    depth = 0
    in_string = False
    escape = False
    i = arr_start
    while i < len(text):
        ch = text[i]
        if escape:
            escape = False
        elif ch == '\\':
            escape = True
        elif ch == '"':
            in_string = not in_string
        elif not in_string:
            if ch == '[':
                depth += 1
            elif ch == ']':
                if depth == 0:
                    break
                depth -= 1
        i += 1
    arr_end = i
    
    header = text[:decl_start]
    decl = text[decl_start:m.end()-1]  # const name = 
    content = text[arr_start:arr_end]
    footer = text[arr_end+1:]
    
    ob = content.count('{')
    cb = content.count('}')
    print(f'  المحتوى: {len(content)} بايت, {{={ob}, }}={cb}, الفرق={ob-cb}')
    
    # Extract items
    items = extract_items(content)
    print(f'  العناصر المستخرجة: {len(items)}')
    
    # Validate each item
    valid = []
    invalid = []
    for idx, item in enumerate(items):
        ok, err = validate_item(item)
        if ok:
            valid.append(item)
        else:
            invalid.append((idx, err, item[:150]))
    
    print(f'  صالح: {len(valid)}, غير صالح: {len(invalid)}')
    
    for idx, err, preview in invalid[:5]:
        print(f'    [{idx}] {err}: {preview}...')
    
    if invalid:
        # Rebuild with only valid items
        rebuilt = ',\n  '.join(valid)
        new_text = header + decl + '[\n  ' + rebuilt + '\n]' + footer
        
        # Verify
        m2 = re.search(r'const\s+\w+\s*=\s*\[', new_text)
        if m2:
            ns = m2.end()
            nd = 0
            in_s = False
            esc = False
            j = ns
            while j < len(new_text):
                c = new_text[j]
                if esc: esc = False
                elif c == '\\': esc = True
                elif c == '"': in_s = not in_s
                elif not in_s:
                    if c == '[': nd += 1
                    elif c == ']':
                        if nd == 0: break
                        nd -= 1
                j += 1
            nc = new_text[ns:j]
            nob = nc.count('{')
            ncb = nc.count('}')
            if nob == ncb:
                tmp = path + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    f.write(new_text)
                os.replace(tmp, path)
                print(f'  ✅ تم الإصلاح ({{={nob}, }}={ncb})')
                return True
            else:
                print(f'  ❌ الإصلاح فشل ({{={nob}, }}={ncb})')
                return False
    else:
        print('  ✅ لا حاجة للإصلاح')
        return True

def main():
    for fp in FILES:
        if os.path.exists(fp):
            fix_file(fp)
        else:
            print(f'❌ غير موجود: {fp}')

if __name__ == '__main__':
    main()
