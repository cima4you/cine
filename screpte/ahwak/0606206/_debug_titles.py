import re, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

def clean_title(t):
    t = re.sub(r'^مسلسل\s+', '', t)
    t = re.sub(r'\s+مترجم\s*$', '', t)
    t = re.sub(r'\s+مدبلج\s*$', '', t)
    t = re.sub(r'\s+مدبلجة\s*$', '', t)
    t = re.sub(r'\s+مترجمة\s*$', '', t)
    t = re.sub(r'\s*-\s*$', '', t)
    t = re.sub(r'\s*\(مترجم\)\s*$', '', t)
    t = re.sub(r'\s*\(مدبلج\)\s*$', '', t)
    if ' - ' in t:
        parts = t.split(' - ', 1)
        first = parts[0].strip()
        latin_count = sum(1 for c in first if c.isascii() and c.isalpha())
        arabic_count = sum(1 for c in first if '\u0600' <= c <= '\u06FF')
        if latin_count > arabic_count:
            t = first
        else:
            second = parts[1].strip()
            latin2 = sum(1 for c in second if c.isascii() and c.isalpha())
            arabic2 = sum(1 for c in second if '\u0600' <= c <= '\u06FF')
            if latin2 > arabic2:
                t = second
    return t.strip()

def norm(t):
    return re.sub(r'[\u064B-\u0652]', '', re.sub(r'\s+', '', (t or '').strip().lower()))

# Check first few titles from both sources
print("=== Existing completed (merged JS) ===")
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-completed.js', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'\[\s*\{', content, re.DOTALL)
start = m.start()
depth = 0
for i in range(start, len(content)):
    if content[i] == '[': depth += 1
    elif content[i] == ']':
        depth -= 1
        if depth == 0:
            existing = json.loads(content[start:i+1])
            break

# Clean existing titles
for x in existing:
    cleaned = clean_title(x.get('title', ''))
    if cleaned != x.get('title', ''):
        x['title'] = cleaned

print("First 5 existing titles:")
for x in existing[:5]:
    print(f"  [{norm(x['title'])}] {x['title'][:50]}")

print()
print("=== Source (full JSON) ===")
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_full.json', 'r', encoding='utf-8') as f:
    source = json.load(f)

print("First 5 source titles (after clean_title):")
for item in source[:5]:
    t = clean_title(item.get('title', ''))
    print(f"  [{norm(t)}] {t[:50]}")

# Now check match rate
exist_map = {norm(x.get('title', '')): x for x in existing}
misses = []
for item in source:
    t = norm(clean_title(item.get('title', '')))
    if t not in exist_map:
        misses.append(item.get('title', '')[:60])

print()
print(f"Misses: {len(misses)} out of {len(source)}")
if misses:
    print("First 10 missed titles:")
    for m in misses[:10]:
        print(f"  {m}")
