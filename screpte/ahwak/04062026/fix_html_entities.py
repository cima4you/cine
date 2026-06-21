import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()

def replace_entity(m):
    return chr(int(m.group(1)))

original = c
c = re.sub(r'&#(\d+);', replace_entity, c)

count = (c != original)
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('Entities replaced. File size before/after:', len(original), len(c))
