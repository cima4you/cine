#!/usr/bin/env python3
"""
تنظيف المدخلات المكررة للمسلسلات.
مشكلة: بعض المسلسلات لها مداخل منفصلة مثل:
  - "الحفرة" (يحتوي كل المواسم)
  - "الحفرة الموسم الثالث" (مكرر جزئي)
  - "الحفرة الموسم الرابع" (مكرر جزئي)

الحل: لكل مجموعة بنفس الإسم الأساسي، نحتفظ بالمدخل الأكثر شمولاً
(أكثر مواسم/حلقات) ونحذف الباقي، مع دمج أي حلقات فريدة أولاً.
"""
import re, json, sys, os, time

sys.stdout.reconfigure(encoding='utf-8')
DATA_DIR = r'D:\web-secriping\Ancien PC\DT\site-rachid\data'

def get_base_title(t):
    """استخراج اسم المسلسل الأساسي بإزالة لاحقة الموسم/الجزء"""
    t = t.strip()
    # Remove season/part suffixes
    t = re.sub(r'\s+(الجزء\s+(الأول|الاول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+))$', '', t)
    t = re.sub(r'\s+(الموسم\s+(الأول|الاول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+))$', '', t)
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

def count_seasons(item):
    return len(item.get('seasons', []))

def get_title_priority(title, base):
    """كلما كان العنوان أقصر وأقرب للإسم الأساسي، كانت أولويته أعلى"""
    t = title.strip()
    b = base.strip()
    if t == b:
        return 0  # Exact match = best
    if t.startswith(b):
        return len(t) - len(b)  # Shorter suffix = better
    return 100

def merge_episodes_into_main(main, other):
    """دمج حلقات unique from other into main"""
    changed = False
    main_seasons = {s.get('seasonNumber', s.get('season', 0)): s for s in main.get('seasons', [])}
    for s in other.get('seasons', []):
        sn = s.get('seasonNumber', s.get('season', 0))
        if sn in main_seasons:
            # Merge episodes by title
            existing_eps = {e.get('title', ''): e for e in main_seasons[sn].get('episodes', [])}
            for ep in s.get('episodes', []):
                et = ep.get('title', '')
                if et in existing_eps:
                    oe = existing_eps[et]
                    ns = ep.get('servers', [])
                    os_ = oe.get('servers', [])
                    if ns and ns != os_:
                        oe['servers'] = ns
                        changed = True
                else:
                    main_seasons[sn].setdefault('episodes', []).append(ep)
                    changed = True
        else:
            # New season from other entry
            # Ensure it has both key names
            if 'season' not in s and 'seasonNumber' in s:
                s['season'] = s['seasonNumber']
            elif 'seasonNumber' not in s and 'season' in s:
                s['seasonNumber'] = s['season']
            main.setdefault('seasons', []).append(s)
            changed = True
    return changed

def pick_main(group):
    """اختيار أفضل مدخل في المجموعة"""
    def key(item):
        return (-count_seasons(item), -count_eps(item), 
                get_title_priority(item.get('title', ''), get_base_title(item.get('title', ''))))
    return min(group, key=key)

def process_file(path, label):
    if not os.path.exists(path):
        print(f'⚠ {label}: الملف غير موجود')
        return None, None, None
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    m = re.search(r'(const|let|var)\s+(\w+)\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
    if m:
        items = json.loads(m.group(3))
        var_name = m.group(2)
    else:
        m = re.search(r'(\[.*?\])\s*;?\s*$', content, re.DOTALL)
        items = json.loads(m.group(1))
        var_name = 'cd_turkish_completed' if 'completed' in path else 'cd_turkish_ongoing'
    
    before = len(items)
    
    # Group by base title
    groups = {}
    for item in items:
        title = item.get('title', '')
        base = get_base_title(title)
        key = norm(base)
        groups.setdefault(key, []).append(item)
    
    # Find groups with duplicates
    dups = {k: v for k, v in groups.items() if len(v) > 1}
    
    if not dups:
        print(f'✅ {label}: لا توجد مكررات')
        return before, before, 0
    
    # Process each duplicate group
    removed = 0
    merged_into = set()  # track items that received merges
    for key, group in dups.items():
        main = pick_main(group)
        main_title = main.get('title', '')
        main_idx = items.index(main)
        
        for other in group:
            if other is main:
                continue
            other_title = other.get('title', '')
            # Try to merge episodes from other into main
            merged = merge_episodes_into_main(main, other)
            if merged:
                merged_into.add(main_title[:40])
            # Remove other from the list
            items.remove(other)
            removed += 1
        
        # Re-sort main's seasons by season number
        main['seasons'].sort(key=lambda s: s.get('seasonNumber', s.get('season', 0)))
    
    after = len(items)
    
    print(f'\n=== {label} ===')
    print(f'  Series: {before} → {after}')
    print(f'  Removed duplicates: {removed}')
    print(f'  Groups processed: {len(dups)}')
    if merged_into:
        print(f'  Merged episodes into:')
        for name in sorted(merged_into):
            print(f'    • {name}')
    
    # Save
    lbl = 'منتهية' if 'completed' in path else 'مستمرة'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات تركية {lbl} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)
    print(f'  ✅ حفظ: {path}')
    
    return before, after, removed

if __name__ == '__main__':
    process_file(os.path.join(DATA_DIR, 'data-turkish-completed.js'), 'المكتملة')
    process_file(os.path.join(DATA_DIR, 'data-turkish-ongoing.js'), 'المستمرة')
    print('\n🎫 تم التنظيف')
