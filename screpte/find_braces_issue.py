import re, os

BASE = r'D:\Users\DT01\Desktop\rachid-site'
path = os.path.join(BASE, r'test\data.js')

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const\s+\w+\s*=\s*\[', text)
start = m.end()
depth = 1
i = start
while i < len(text) and depth > 0:
    c = text[i]
    if c == '[':
        depth += 1
    elif c == ']':
        depth -= 1
    i += 1
end = i - 1
content = text[start:end]

# Find transition from compact new content to pretty old content
# Search for },\n  { which is the boundary
transition = content.find(',\n  {')
if transition < 0:
    transition = content.find('},\n')

if transition >= 0:
    # Look at a wider window around transition
    window_start = max(0, transition - 500)
    window_end = min(len(content), transition + 2000)
    snippet = content[window_start:window_end]
    
    # Count braces in this snippet
    ob = snippet.count('{')
    cb = snippet.count('}')
    print(f'Transition at offset {transition}')
    print(f'Window braces: open={ob}, close={cb}, diff={ob-cb}')
    
    # Write to file for inspection
    out = os.path.join(r'C:\Users\DT01\AppData\Local\Temp\opencode', 'transition_debug.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(f'Transition at offset {transition}\n')
        f.write(f'Window ({window_start}-{window_end}), braces diff={ob-cb}\n\n')
        f.write(snippet)
    print(f'Written to {out}')
    
    # Also find the exact brace balance around the new content
    # New content goes from 0 to transition
    new_part = content[:transition]
    old_part = content[transition:]
    
    nob = new_part.count('{')
    ncb = new_part.count('}')
    print(f'New part (0-{transition}): open={nob}, close={ncb}, diff={nob-ncb}')
    
    oob = old_part.count('{')
    ocb = old_part.count('}')
    print(f'Old part ({transition}-end): open={oob}, close={ocb}, diff={oob-ocb}')
else:
    print('No transition found, checking entire content...')
    newline_counts = content.count('\n')
    print(f'Content has {newline_counts} newlines')
    
    # Try to find the last entry before closing
    out = os.path.join(r'C:\Users\DT01\AppData\Local\Temp\opencode', 'no_transition_debug.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(content[-500:])
    print(f'Last 500 chars written to {out}')
