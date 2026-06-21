import re, os

BASE = r'D:\Users\DT01\Desktop\rachid-site'
path = os.path.join(BASE, r'test\data.js')

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Find the key transition point
# Look for where new content ends and old content begins
# Find the array boundaries
m = re.search(r'(const\s+\w+\s*=\s*)\[', text)
if m:
    start = m.end()
    # Count brackets to find end
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        i += 1
    end = i - 1
    
    # Check the first 500 chars of the array
    content = text[start:end]
    print('Array content length:', len(content))
    
    # Find where "},\n  {" pattern appears - transition from compact to pretty
    transition = content.find(',\n  {')
    if transition > 0:
        # Check around the transition
        before = content[max(0,transition-100):transition+100]
        # Print without escaping issues
        with open(r'C:\Users\DT01\AppData\Local\Temp\opencode\transition_check.txt', 'w', encoding='utf-8') as f:
            f.write(f'Transition at position {transition}:\n')
            f.write(before)
        print('Transition written to file')
    else:
        print('No transition found - checking structure...')
        # Check if this is all compact
        with open(r'C:\Users\DT01\AppData\Local\Temp\opencode\transition_check.txt', 'w', encoding='utf-8') as f:
            f.write(content[:2000])
        print('First 2000 chars written to file')
