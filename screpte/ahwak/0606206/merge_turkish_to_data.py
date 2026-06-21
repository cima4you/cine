#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge scraped Turkish series data into modular data files.
- Reads screpte/ahwak/0606206/ahwaktv_data_formatted.json
- Cleans titles, deduplicates, adds isComplete
- Merges into data/data-turkish-completed.js / ongoing.js
Usage:
    python merge_turkish_to_data.py
    python merge_turkish_to_data.py --source screpte/ahwak/0606206/ahwaktv_data_formatted.json
"""
import os, sys, json, re, time, argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

COMPLETED_FILE = os.path.join(DATA_DIR, 'data-turkish-completed.js')
ONGOING_FILE = os.path.join(DATA_DIR, 'data-turkish-ongoing.js')
DEFAULT_SOURCE = os.path.join(SCRIPT_DIR, 'ahwaktv_data_formatted.json')

def p(text, **kwargs):
    try: print(text, flush=True, **kwargs)
    except: print(repr(text), flush=True)

def clean_title(t):
    t = re.sub(r'^مسلسل\s+', '', t)
    t = re.sub(r'\s+مترجم\s*$', '', t)
    t = re.sub(r'\s+مدبلج\s*$', '', t)
    t = re.sub(r'\s+مدبلجة\s*$', '', t)
    t = re.sub(r'\s+مترجمة\s*$', '', t)
    t = re.sub(r'\s*-\s*$', '', t)
    t = re.sub(r'\s*\(مترجم\)\s*$', '', t)
    t = re.sub(r'\s*\(مدبلج\)\s*$', '', t)
    # For mixed titles like "Arayis - البحث (مترجم)", take the first part
    if ' - ' in t:
        parts = t.split(' - ', 1)
        first = parts[0].strip()
        latin_count = sum(1 for c in first if c.isascii() and c.isalpha())
        arabic_count = sum(1 for c in first if '\u0600' <= c <= '\u06FF')
        if latin_count > arabic_count:
            t = first
        else:
            # If second part has more latin chars, take it
            second = parts[1].strip()
            latin2 = sum(1 for c in second if c.isascii() and c.isalpha())
            arabic2 = sum(1 for c in second if '\u0600' <= c <= '\u06FF')
            if latin2 > arabic2:
                t = second
    return t.strip()

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
        result.append(max(group, key=count_eps))
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
    items = json.loads(m.group(2))
    return items, m.group(1), content[:m.start(2)]

def save_data_js(path, items, var_name, header):
    label = 'منتهية' if 'completed' in path else 'مستمرة'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات تركية {label} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)
    p(f'📁 حفظ: {path} ({len(items)} عنصر)')

def merge_into(existing, new_items):
    # Clean existing titles too
    for x in existing:
        cleaned = clean_title(x.get('title', ''))
        if cleaned != x.get('title', ''):
            x['title'] = cleaned
    norm = lambda t: re.sub(r'[\u064B-\u0652]', '', re.sub(r'\s+', '', (t or '').strip().lower()))
    exist_map = {norm(x.get('title', '')): x for x in existing}
    added = 0
    updated = 0
    added_names = []
    updated_names = []
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
                old_seasons = {}
                for s_old in old.get('seasons', []):
                    sk = s_old.get('seasonNumber', s_old.get('season', 0))
                    old_seasons[sk] = s_old
                for s in item['seasons']:
                    sn = s.get('seasonNumber', 0) or s.get('season', 0)
                    if sn in old_seasons:
                        old_eps = {e.get('title', ''): e for e in old_seasons[sn].get('episodes', [])}
                        for e in s.get('episodes', []):
                            et = e.get('title', '')
                            if et in old_eps:
                                oe = old_eps[et]
                                ns = e.get('servers', [])
                                os = oe.get('servers', [])
                                if ns and ns != os:
                                    oe['servers'] = ns
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
                updated_names.append(item.get('title', '')[:40])
        else:
            item.setdefault('type', 'تركي')
            item.setdefault('contentType', 'series')
            existing.append(item)
            added += 1
            added_names.append(item.get('title', '')[:40])
    if added_names:
        p('  ➕ جديد:')
        for name in added_names:
            p(f'    • {name}')
    if updated_names:
        p('  🔄 محدث:')
        for name in updated_names:
            p(f'    • {name}')
    return existing, added, updated

def main():
    parser = argparse.ArgumentParser(description='دمج بيانات المسلسلات التركية')
    parser.add_argument('--source', default=DEFAULT_SOURCE)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.source):
        p(f'❌ الملف غير موجود: {args.source}')
        sys.exit(1)

    raw = open(args.source, 'r', encoding='utf-8').read()
    raw = re.sub(r',\s*\]', ']', raw)
    raw = json.loads(raw)
    p(f'📂 تم تحميل {len(raw)} مسلسل من {args.source}')

    raw = add_iscomplete(raw)

    # Normalize each item: ensure episodeNumber exists
    for item in raw:
        for s in item.get('seasons', []):
            for e in s.get('episodes', []):
                if 'episodeNumber' not in e:
                    e['episodeNumber'] = e.get('number', 0)
                if 'number' not in e:
                    e['number'] = e.get('episodeNumber', 0)

    raw = deduplicate(raw)
    for item in raw:
        item['title'] = clean_title(item['title'])
        if item.get('description'):
            desc = clean_title(item['description'])
            if desc:
                item['description'] = desc
    p(f'🧹 بعد التنظيف وإزالة التكرار: {len(raw)} مسلسل')

    completed = [x for x in raw if x.get('isComplete')]
    ongoing = [x for x in raw if not x.get('isComplete')]
    p(f'📊 مكتمل: {len(completed)} | مستمر: {len(ongoing)}')

    if args.dry_run:
        p('🧪 Dry-run — لم يتم حفظ شيء')
        return

    for file_path, new_items, label in [
        (COMPLETED_FILE, completed, 'المكتملة'),
        (ONGOING_FILE, ongoing, 'المستمرة'),
    ]:
        existing, var_name, _ = load_data_js(file_path)
        if existing:
            p(f'📂 {label}: تحميل {len(existing)} عنصر من {file_path}')
        else:
            p(f'📂 {label}: ملف جديد')
            var_name = 'cd_turkish_completed' if 'completed' in file_path else 'cd_turkish_ongoing'

        merged, added, updated = merge_into(existing, new_items)
        p(f'✅ {label}: جديد {added} | محدث {updated} | الإجمالي {len(merged)}')
        save_data_js(file_path, merged, var_name, '')

    # Update data-loader.js if needed
    loader = os.path.join(DATA_DIR, 'data-loader.js')
    if os.path.exists(loader):
        lc = open(loader, 'r', encoding='utf-8').read()
        for var in ['cd_turkish_completed', 'cd_turkish_ongoing']:
            if var not in lc:
                p(f'⚠ {var} غير موجود في data-loader.js — أضفه يدوياً')

    p('🎉 تم دمج جميع المسلسلات التركية')

if __name__ == '__main__':
    main()
