import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

def get_base_title(t):
    """Extract base series name by removing season/part suffixes"""
    t = t.strip()
    # Remove patterns like " الجزء الأول", " الجزء 1", " الموسم الأول", " الموسم 3", etc.
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

# Parse both files
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
    
    # Group by base title
    groups = {}
    for item in items:
        title = item.get('title', '')
        base = get_base_title(title)
        key = norm(base)
        groups.setdefault(key, []).append(item)
    
    # Find groups with more than one entry
    dups = {k: v for k, v in groups.items() if len(v) > 1}
    
    print(f"\n=== {label} ({len(items)} series) ===")
    print(f"Groups with duplicates: {len(dups)}")
    
    if dups:
        for k, group in sorted(dups.items()):
            print(f"\n  Base: {group[0]['title'][:40]}")
            for item in sorted(group, key=lambda x: -count_eps(x)):
                title = item.get('title', '')[:50]
                eps = count_eps(item)
                seasons = len(item.get('seasons', []))
                print(f"    - '{title}' ({seasons} مواسم, {eps} حلقة)")
