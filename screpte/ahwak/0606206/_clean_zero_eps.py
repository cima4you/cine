import re, json, sys, os, time

sys.stdout.reconfigure(encoding='utf-8')
DATA_DIR = r'D:\web-secriping\Ancien PC\DT\site-rachid\data'

def get_base_title(t):
    t = t.strip()
    t = re.sub(r'\s+(الجزء\s+(الأول|الاول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+))$', '', t)
    t = re.sub(r'\s+(الموسم\s+(الأول|الاول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+))$', '', t)
    t = re.sub(r'\s*[-\u2013]\s*(الجزء|ج\d+|season\s*\d+)$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+(موسم)\s*$', '', t)
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

def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
    if m:
        items = json.loads(m.group(2))
        var_name = m.group(1)
        header_end = m.start(2)
    else:
        m = re.search(r'(\[.*?\])\s*;?\s*$', content, re.DOTALL)
        items = json.loads(m.group(1))
        var_name = 'cd_turkish_completed'
    return items, var_name

def save(path, items, var_name, label):
    lbl = 'منتهية' if 'completed' in path else 'مستمرة'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات تركية {lbl} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)
    print(f'  ✅ {label}: {len(items)} عنصر')

# Load both files
completed, _ = load(os.path.join(DATA_DIR, 'data-turkish-completed.js'))
ongoing, var_name = load(os.path.join(DATA_DIR, 'data-turkish-ongoing.js'))

# Build set of bases that exist in completed (with episodes)
completed_bases = set()
for item in completed:
    if count_eps(item) > 0:
        base = get_base_title(item.get('title', ''))
        completed_bases.add(norm(base))

# Find entries in ongoing that should be removed
removed = []
kept = []
zero_in_ongoing = []
dup_in_ongoing = []

for item in ongoing:
    eps_count = count_eps(item)
    title = item.get('title', '')
    base = get_base_title(title)
    key = norm(base)
    
    if eps_count == 0:
        zero_in_ongoing.append(item)
        # Remove if its base exists in completed (has episodes there)
        if key in completed_bases:
            removed.append((title, 'موجود في المكتملة'))
            continue
        # Also check if same base exists with eps in ongoing itself
        # (handled by dedup below)
    
    kept.append(item)

# Now check for duplicates within ongoing (same base, both have 0 eps)
groups = {}
for item in zero_in_ongoing:
    if item.get('title') in [r[0] for r in removed]:
        continue  # Already removed
    base = get_base_title(item.get('title', ''))
    key = norm(base)
    groups.setdefault(key, []).append(item)

for key, group in groups.items():
    if len(group) > 1:
        # Keep one, remove the rest
        for item in group[1:]:
            removed.append((item.get('title', ''), 'مكرر داخل المستمرة'))
            if item in kept:
                kept.remove(item)

before = len(ongoing)
after = len(kept)

print(f"=== المستمرة ===")
print(f"  Before: {before}")
print(f"  After: {after}")
print(f"  Removed: {len(removed)}")
print(f"  Zero-episode remaining: {sum(1 for item in kept if count_eps(item) == 0)}")

if removed:
    print(f"\n  المحذوفة:")
    for title, reason in sorted(removed):
        print(f"    • {title[:45]} — {reason}")

# Save
save(os.path.join(DATA_DIR, 'data-turkish-ongoing.js'), kept, var_name, 'المستمرة')
save(os.path.join(DATA_DIR, 'data-turkish-completed.js'), completed, 'cd_turkish_completed', 'المكتملة')
