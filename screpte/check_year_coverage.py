import re, sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Users\DT01\Desktop\rachid-site\test\data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the array interior
m = re.search(r'const\s+\w+\s*=\s*\[', content)
start = m.end()

depth = 0
in_s = False
esc = False
i = start
while i < len(content):
    c = content[i]
    if esc: esc = False
    elif c == '\\': esc = True
    elif c == '"': in_s = not in_s
    elif not in_s:
        if c == '[': depth += 1
        elif c == ']':
            if depth == 0: break
            depth -= 1
    i += 1

array_body = content[start:i]

# Count entries by finding top-level brace pairs  
entry_count = 0
depth = 0
for c in array_body:
    if in_s:
        if c == '\\': esc = not esc
        elif c == '"' and not esc: in_s = not in_s
        else: esc = False
        continue
    if c == '\\': esc = not esc; continue
    if c == '"': in_s = True; continue
    if c == '{': depth += 1
    elif c == '}': depth -= 1; 
    
esc = False
in_s = False
entry_count = 0
has_year_count = 0
for c in array_body:
    if esc: esc = False; continue
    if c == '\\': esc = True; continue
    if c == '"': in_s = not in_s; continue
    if in_s: continue
    
    if c == '{': depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            entry_count += 1

# Simpler approach: count entries by number of } that bring depth to 0
# and count "year": occurrences
year_count = len(re.findall(r'\byear\s*:', array_body))

print(f"Total entries: ~{entry_count}")
print(f"'year' field occurrences: {year_count}")
print(f"Entries without year: {entry_count - year_count}")
