import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

def get_base_title(t):
    t = t.strip()
    t = re.sub(r'\s+(الجزء\s+(الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+))$', '', t)
    t = re.sub(r'\s+(الموسم\s+(الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+))$', '', t)
    t = re.sub(r'\s+[-\u2013]\s*(الجزء|ج\d+|season\s*\d+)$', '', t, flags=re.IGNORECASE)
    return t.strip()

def norm(t):
    t = re.sub(r'^مسلسل\s+', '', t)
    t = re.sub(r'\s+مترجم\s*$', '', t)
    t = re.sub(r'\s+مدبلج\s*$', '', t)
    t = re.sub(r'\s+مدبلجة\s*$', '', t)
    t = re.sub(r'\s+مترجمة\s*$', '', t)
    t = re.sub(r'\s*-\s*$', '', t)
    t = re.sub(r'\s*\(مترجم\)\s*$', '', t)
    t = re.sub(r'\s*\(مدبلج\)\s*$', '', t)
    t = re.sub(r'\s*\(مدبلجة\)\s*$', '', t)
    t = re.sub(r'\s*\(مترجمة\)\s*$', '', t)
    return re.sub(r'\s+', '', (t or '').strip().lower())

def count_eps(item):
    return sum(len(s.get('episodes', [])) for s in item.get('seasons', []))

for fname, label in [
    (r'D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-completed.js', 'المكتملة'),
    (r'D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-ongoing.js', 'المستمرة'),
]:
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'\[\s*\{', content, re.DOTALL)
    start = m.start()
    depth = 0
    for i in range(start, len(content)):
        if content[i] == '[': depth += 1
        elif content[i] == ']':
            depth -= 1
            if depth == 0:
                items = json.loads(content[start:i+1])
                break
    
    # Find zero-episode entries
    zero_eps = [item for item in items if count_eps(item) == 0]
    
    # Check for remaining duplicate bases
    groups = {}
    for item in items:
        base = get_base_title(item.get('title', ''))
        key = norm(base)
        groups.setdefault(key, []).append(item)
    
    dups = {k: v for k, v in groups.items() if len(v) > 1}
    
    print(f"=== {label} ===")
    print(f"Total: {len(items)}")
    print(f"Zero-episode entries: {len(zero_eps)}")
    if zero_eps:
        for item in zero_eps:
            title = item.get('title', '')[:50]
            print(f"  - '{title}'")
    print(f"Remaining duplicate bases: {len(dups)}")
    for k, group in dups.items():
        names = [item.get('title', '')[:40] for item in group]
        print(f"  - {names[0]} ({len(group)} entries)")
    print()
