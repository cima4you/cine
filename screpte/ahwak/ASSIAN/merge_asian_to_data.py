#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge scraped Asian series data into modular data files.
- Reads screpte/ahwak/ASSIAN/asian_series_full.json
- Cleans titles, deduplicates, adds isComplete
- Merges into data/data-asian-series-completed.js / ongoing.js
Usage:
    python merge_asian_to_data.py
    python merge_asian_to_data.py --source screpte/ahwak/ASSIAN/asian_series_full.json
    python merge_asian_to_data.py --dry-run
"""
import os, sys, json, re, time, argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))  # site-rachid/
DATA_DIR = BASE_DIR

COMPLETED_FILE = os.path.join(DATA_DIR, 'data-asian-series-completed.js')
ONGOING_FILE = os.path.join(DATA_DIR, 'data-asian-series-ongoing.js')
DEFAULT_SOURCE = os.path.join(SCRIPT_DIR, 'asian_series_full.json')

def p(text, **kwargs):
    try: print(text, flush=True, **kwargs)
    except: print(repr(text), flush=True)

def clean_title(t):
    t = re.sub(r'^مسلسل\s+', '', t)
    t = re.sub(r'\s+مترجم\s*$', '', t)
    t = re.sub(r'\s+مدبلج\s*$', '', t)
    if ' - ' in t:
        parts = t.split(' - ', 1)
        first = parts[0].strip()
        latin_count = sum(1 for c in first if c.isascii() and c.isalpha())
        if latin_count > len(first) * 0.6:
            t = first
    return t.strip()

def clean_description(d):
    return clean_title(d)

def count_eps(item):
    return sum(len(s.get('episodes', [])) for s in item.get('seasons', []))

def deduplicate(items):
    groups = {}
    for item in items:
        key = clean_title(item.get('title', '')).lower()
        key = re.sub(r'[\u064B-\u0652]', '', key)
        key = re.sub(r'\s+', '', key)
        groups.setdefault(key, []).append(item)
    result = []
    for key, group in groups.items():
        best = max(group, key=count_eps)
        result.append(best)
    return result

def add_iscomplete(items):
    for item in items:
        has_final_ep = any(
            'الاخيرة' in e.get('title', '') or 'الأخيرة' in e.get('title', '')
            for s in item.get('seasons', [])
            for e in s.get('episodes', [])
        )
        has_final_title = any(
            w in item.get('title', '')
            for w in ['الاخيرة', 'والاخيرة', 'الأخيرة', 'والأخيرة', 'كاملة', 'كامله']
        )
        item['isComplete'] = has_final_ep or has_final_title
    return items

def load_data_js(path):
    if not os.path.exists(path):
        return [], None, None
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
    if not m:
        p(f'⚠ لم يتم العثور على مصفوفة في {path}')
        return [], None, None
    var_name = m.group(1)
    items = json.loads(m.group(2))
    return items, var_name, content[:m.start(2)]

def save_data_js(path, items, var_name, header):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات آسيوية منتهية — {len(items)} عنصر\n' if 'completed' in path else f'// مسلسلات آسيوية مستمرة — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)
    p(f'📁 حفظ: {path} ({len(items)} عنصر)')

def merge_into(existing, new_items, updated_existing_keys):
    norm = lambda t: re.sub(r'[\u064B-\u0652]', '', re.sub(r'\s+', '', (t or '').strip().lower()))
    # Clean existing titles that may have مسلسل prefix or other artifacts
    for x in existing:
        cleaned = clean_title(x.get('title', ''))
        if cleaned != x.get('title', ''):
            x['title'] = cleaned
    exist_map = {norm(x.get('title', '')): x for x in existing}
    added = 0
    updated = 0
    for item in new_items:
        t = norm(item.get('title', ''))
        if t in exist_map:
            old = exist_map[t]
            changed = False
            for key in ('poster', 'description', 'year', 'type'):
                if key in item and item[key] != old.get(key):
                    old[key] = item[key]
                    changed = True
            if 'seasons' in item and item['seasons']:
                old_seasons = {s.get('season', 0): s for s in old.get('seasons', [])}
                for s in item['seasons']:
                    sn = s.get('season', 0)
                    if sn in old_seasons:
                        old_eps = {e.get('title', ''): e for e in old_seasons[sn].get('episodes', [])}
                        for e in s.get('episodes', []):
                            et = e.get('title', '')
                            if et in old_eps:
                                oe = old_eps[et]
                                if e.get('servers') and e['servers'] != oe.get('servers'):
                                    oe['servers'] = e['servers']
                                    changed = True
                                if e.get('downloadServers') and e['downloadServers'] != oe.get('downloadServers'):
                                    oe['downloadServers'] = e['downloadServers']
                                    changed = True
                            else:
                                old_seasons[sn].setdefault('episodes', []).append(e)
                                changed = True
                    else:
                        old.setdefault('seasons', []).append(s)
                        changed = True
            if 'isComplete' in item and item['isComplete'] != old.get('isComplete'):
                old['isComplete'] = item['isComplete']
                changed = True
            if changed:
                updated += 1
        else:
            existing.append(item)
            added += 1
    return existing, added, updated

def main():
    parser = argparse.ArgumentParser(description='دمج بيانات المسلسلات الأسوية')
    parser.add_argument('--source', default=DEFAULT_SOURCE)
    parser.add_argument('--dry-run', action='store_true', help='عرض فقط بدون كتابة')
    args = parser.parse_args()

    if not os.path.exists(args.source):
        p(f'❌ الملف غير موجود: {args.source}')
        sys.exit(1)

    with open(args.source, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    p(f'📂 تم تحميل {len(raw)} مسلسل من {args.source}')

    raw = add_iscomplete(raw)
    raw = deduplicate(raw)
    for item in raw:
        item['title'] = clean_title(item['title'])
        if item.get('description'):
            item['description'] = clean_description(item['description'])
    p(f'🧹 بعد التنظيف وإزالة التكرار: {len(raw)} مسلسل')

    completed = [x for x in raw if x.get('isComplete')]
    ongoing = [x for x in raw if not x.get('isComplete')]
    p(f'📊 مكتمل: {len(completed)} | مستمر: {len(ongoing)}')

    if args.dry_run:
        p('🧪 Dry-run — لم يتم حفظ أي شيء')
        return

    for file_path, new_items, label in [
        (COMPLETED_FILE, completed, 'المكتملة'),
        (ONGOING_FILE, ongoing, 'المستمرة'),
    ]:
        existing, var_name, _ = load_data_js(file_path)
        if existing:
            p(f'📂 {label}: تحميل {len(existing)} عنصر من {file_path}')
        else:
            p(f'📂 {label}: ملف جديد — إنشاء {len(new_items)} عنصر')
            var_name = 'cd_asian_series_completed' if 'completed' in file_path else 'cd_asian_series_ongoing'

        merged, added, updated = merge_into(existing, new_items, set())
        p(f'✅ {label}: جديد {added} | محدث {updated} | الإجمالي {len(merged)}')
        save_data_js(file_path, merged, var_name, '')

    p('🎉 تم دمج جميع المسلسلات الأسوية')

if __name__ == '__main__':
    main()
