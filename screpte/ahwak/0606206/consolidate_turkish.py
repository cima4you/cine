#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidate Turkish series data: merge entries split across completed/ongoing,
combine all episodes, determine isComplete properly.
"""
import os, re, json, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
DATA_DIR = BASE_DIR

COMPLETED_FILE = os.path.join(DATA_DIR, 'data-turkish-completed.js')
ONGOING_FILE = os.path.join(DATA_DIR, 'data-turkish-ongoing.js')

def arabic_only(text):
    return re.sub(r'[^\u0600-\u06FF\s]', '', text).strip()

def choose_best_title(titles):
    latin_titles = [t for t in titles if re.search(r'[a-zA-Z]', t)]
    if latin_titles:
        return max(latin_titles, key=len)
    return max(titles, key=len)

def load_js(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(\[.*\])\s*;?\s*$', content, re.DOTALL)
    if not m:
        m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(\[.*\])\s*$', content, re.DOTALL)
    return json.loads(m.group(2)), m.group(1)

def save_js(path, items, var_name, label):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات تركية {label} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)
    print(f'  Saved: {path} ({len(items)} items)')

def collect_episodes(entries):
    """Collect all unique episodes from a list of entries."""
    all_eps = {}
    for entry in entries:
        for s in entry.get('seasons', []):
            for ep in s.get('episodes', []):
                ep_num = ep.get('episodeNumber') or ep.get('number', 0)
                if ep_num and ep_num not in all_eps:
                    all_eps[ep_num] = ep
    return sorted(all_eps.values(), key=lambda e: e.get('episodeNumber', 0) or e.get('number', 0))

def determine_complete(eps, title):
    has_final_ep = any(
        'الاخيرة' in e.get('title', '') or 'الأخيرة' in e.get('title', '')
        for e in eps
    ) or any(
        w in title for w in ['الاخيرة', 'والاخيرة', 'الأخيرة', 'والأخيرة', 'كاملة', 'كامله']
    )
    return has_final_ep

def main():
    comp_items, comp_var = load_js(COMPLETED_FILE)
    ongo_items, ongo_var = load_js(ONGOING_FILE)
    
    print(f'Completed: {len(comp_items)} items')
    print(f'Ongoing: {len(ongo_items)} items')
    
    # Group ALL items by Arabic-only name
    groups = {}
    for item in comp_items + ongo_items:
        key = arabic_only(item.get('title', ''))
        groups.setdefault(key, []).append(item)
    
    # Find groups split across files
    split = {k: v for k, v in groups.items() if len(v) > 1}
    print(f'Split groups: {len(split)}')
    
    # Consolidate: merge episodes and determine isComplete
    consolidated = []
    for key, entries in groups.items():
        all_titles = [e.get('title', '') for e in entries]
        best_title = choose_best_title(all_titles)
        all_eps = collect_episodes(entries)
        
        # Find the entry with the best metadata
        best_meta = max(entries, key=lambda x: (
            len(x.get('poster', '')),
            1 if x.get('description') else 0,
            sum(len(s.get('episodes', [])) for s in x.get('seasons', []))
        ))
        
        is_complete = determine_complete(all_eps, best_title)
        
        new_item = {
            'title': best_title,
            'year': best_meta.get('year', ''),
            'rating': best_meta.get('rating', ''),
            'type': 'تركي',
            'contentType': 'series',
            'description': best_meta.get('description', ''),
            'poster': best_meta.get('poster', ''),
            'isComplete': is_complete,
            'seasons': [{
                'season': 1,
                'episodes': all_eps
            }]
        }
        consolidated.append(new_item)
    
    print(f'Consolidated: {len(consolidated)} total')
    
    # Sort by title
    consolidated.sort(key=lambda x: x.get('title', ''))
    
    # Split completed/ongoing
    completed = [x for x in consolidated if x.get('isComplete')]
    ongoing = [x for x in consolidated if not x.get('isComplete')]
    
    print(f'Completed: {len(completed)}, Ongoing: {len(ongoing)}')
    
    save_js(COMPLETED_FILE, completed, comp_var, 'منتهية')
    save_js(ONGOING_FILE, ongoing, ongo_var, 'مستمرة')
    
    print('Done!')

if __name__ == '__main__':
    main()
