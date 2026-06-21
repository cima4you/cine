#!/usr/bin/env python3
"""
سكربت تنظيف الـ duplicate seasons في ملفات البيانات المدمجة.
سبب التكرار: merge_with_existing() كانت تستخدم s.get('season', 0)
بدل s.get('seasonNumber', 0)، مما أدى إلى إضافة مواسم جديدة بدل تحديثها.

العلاج: لكل مسلسل، ندمج الـ episodes من المواسم المكررة (نفس الرقم)
في موسم واحد، ونحذف المكرر.
"""
import re, json, sys, os, time

sys.stdout.reconfigure(encoding='utf-8')
DATA_DIR = r'D:\web-secriping\Ancien PC\DT\site-rachid\data'

def dedup_seasons(items):
    fixed = 0
    for item in items:
        seasons = item.get('seasons', [])
        if len(seasons) <= 1:
            continue
        
        # Group seasons by their number
        seen = {}
        new_seasons = []
        has_dupes = False
        
        for s in seasons:
            sn = s.get('seasonNumber', s.get('season', None))
            if sn is None:
                # Keep as-is if no identifier
                new_seasons.append(s)
                continue
            
            if sn in seen:
                has_dupes = True
                # Merge episodes from the duplicate into the kept season
                existing_eps = seen[sn].get('episodes', [])
                existing_titles = {e.get('title', ''): e for e in existing_eps}
                for ep in s.get('episodes', []):
                    et = ep.get('title', '')
                    if et in existing_titles:
                        oe = existing_titles[et]
                        ns = ep.get('servers', [])
                        os_ = oe.get('servers', [])
                        if ns and ns != os_:
                            oe['servers'] = ns
                    else:
                        existing_eps.append(ep)
                # Update episodes in the kept season
                seen[sn]['episodes'] = existing_eps
            else:
                # Ensure both season key names exist
                if 'season' not in s and 'seasonNumber' in s:
                    s['season'] = s['seasonNumber']
                elif 'seasonNumber' not in s and 'season' in s:
                    s['seasonNumber'] = s['season']
                seen[sn] = s
                new_seasons.append(s)
        
        if has_dupes:
            item['seasons'] = new_seasons
            fixed += 1
    
    return fixed

def process_file(path, label):
    if not os.path.exists(path):
        print(f'⚠ {label}: الملف غير موجود: {path}')
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    m = re.search(r'(const|let|var)\s+(\w+)\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
    if not m:
        # Try broader pattern
        m = re.search(r'(\[.*?\])\s*;?\s*$', content, re.DOTALL)
        if not m:
            print(f'⚠ {label}: لم يتم العثور على JSON')
            return
        items = json.loads(m.group(1))
        var_name = 'cd_turkish_completed'
        header_end = m.start(1)
    else:
        items = json.loads(m.group(3))
        var_name = m.group(2)
        header_end = m.start(3)
    
    before = len(items)
    total_eps_before = sum(
        sum(len(s.get('episodes', [])) for s in item.get('seasons', []))
        for item in items
    )
    
    fixed = dedup_seasons(items)
    
    after = len(items)
    total_eps_after = sum(
        sum(len(s.get('episodes', [])) for s in item.get('seasons', []))
        for item in items
    )
    
    print(f'\n=== {label} ===')
    print(f'  Series: {before} → {after}')
    print(f'  Episodes: {total_eps_before} → {total_eps_after}')
    print(f'  Fixed (had dup seasons): {fixed}')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات تركية {("منتهية" if "completed" in path else "مستمرة")} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)
    print(f'  ✅ حفظ: {path}')

if __name__ == '__main__':
    process_file(os.path.join(DATA_DIR, 'data-turkish-completed.js'), 'المكتملة')
    process_file(os.path.join(DATA_DIR, 'data-turkish-ongoing.js'), 'المستمرة')
    print('\n🎉 تم التنظيف')
