#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean up old Turkish data files that have episode-level entries.
Groups all episode entries under their series name into a single entry.
"""
import os, re, json, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def clean_title(t):
    t = re.sub(r'^مسلسل\s+', '', t)
    t = re.sub(r'\s+مترجم\s*$', '', t)
    t = re.sub(r'\s+مدبلج\s*$', '', t)
    t = re.sub(r'\s+مدبلجة\s*$', '', t)
    t = re.sub(r'\s+مترجمة\s*$', '', t)
    t = re.sub(r'\s*-\s*$', '', t)
    t = re.sub(r'\s*\(مترجم\)\s*$', '', t)
    t = re.sub(r'\s*\(مدبلج\)\s*$', '', t)
    return t.strip()

def extract_series_name(title):
    """Extract base series name from an episode-level title like 'أخي الحلقة 12 الثانية عشر مترجمة HD'"""
    t = clean_title(title)
    # Remove everything from " الحلقة " onwards
    t = re.sub(r'\s*الحلقة\s*\d+.*$', '', t).strip()
    # Remove episode patterns like " 1 ", " 2 " at end (for short titles like "المنظمة 179")
    t = re.sub(r'\s+\d+\s*$', '', t).strip()
    return t

def arabic_only(text):
    """Keep only Arabic characters and spaces for matching."""
    return re.sub(r'[^\u0600-\u06FF\s]', '', text).strip()

def choose_best_title(titles):
    """Pick the best title: prefer one with an English suffix (Latin chars), then longest."""
    latin_titles = [t for t in titles if re.search(r'[a-zA-Z]', t)]
    if latin_titles:
        return max(latin_titles, key=len)
    return max(titles, key=len)

def load_data_js(path):
    if not os.path.exists(path):
        return [], None, None
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Match: const varname = [...];
    m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(\[.*\])\s*;?\s*$', content, re.DOTALL)
    if not m:
        # Try without trailing semicolon
        m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(\[.*\])\s*$', content, re.DOTALL)
    if not m:
        print(f'Could not parse {path}')
        return [], None, None
    try:
        items = json.loads(m.group(2))
    except json.JSONDecodeError as e:
        print(f'JSON error in {path}: {e}')
        return [], None, None
    var_name = m.group(1)
    header_end = m.start(2)
    header = content[:header_end]
    return items, var_name, header

def save_data_js(path, items, var_name, label):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات تركية {label} — {len(items)} عنصر\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(items, f, ensure_ascii=False)
    print(f'  Saved: {path} ({len(items)} items)')

def main():
    for fname, label in [('data-turkish-completed.js', 'منتهية'), ('data-turkish-ongoing.js', 'مستمرة')]:
        fpath = os.path.join(DATA_DIR, fname)
        items, var_name, _ = load_data_js(fpath)
        if not items:
            print(f'{fname}: no items or parse error')
            continue
        
        print(f'\n{fname}: {len(items)} entries before cleanup')
        
        # Group by extracted series name
        groups = {}
        for item in items:
            raw_title = item.get('title', '')
            series = extract_series_name(raw_title)
            if not series:
                series = raw_title
            groups.setdefault(series, []).append(item)
        
        # Count how many groups have multiple entries
        multi = {k: v for k, v in groups.items() if len(v) > 1}
        print(f'  Groups with multiple entries: {len(multi)}')
        for s, ents in sorted(multi.items(), key=lambda x: -len(x[1]))[:10]:
            print(f'    "{s}" -> {len(ents)} entries')
        
        # Merge each group into a single series
        merged_groups = []
        for series_name, entries in groups.items():
            # Find the best entry (most complete)
            best = max(entries, key=lambda x: sum(
                len(s.get('episodes', [])) for s in x.get('seasons', [])
            ))
            
            # Collect all episodes from all entries into season 1
            all_eps = {}
            for entry in entries:
                for s in entry.get('seasons', []):
                    for ep in s.get('episodes', []):
                        ep_num = ep.get('episodeNumber') or ep.get('number', 0)
                        if ep_num and ep_num not in all_eps:
                            all_eps[ep_num] = ep
            
            if all_eps:
                sorted_eps = sorted(all_eps.values(), key=lambda e: e.get('episodeNumber', 0) or e.get('number', 0))
            else:
                sorted_eps = best.get('seasons', [{}])[0].get('episodes', []) if best.get('seasons') else []
            
            # Update best entry with merged episodes
            best['title'] = series_name
            best['seasons'] = [{
                'season': 1,
                'episodes': sorted_eps
            }]
            best['isComplete'] = any(
                'الاخيرة' in e.get('title', '') or 'الأخيرة' in e.get('title', '') or 'كاملة' in e.get('title', '')
                for e in sorted_eps
            ) or any(w in series_name for w in ['الاخيرة', 'والاخيرة', 'الأخيرة', 'والأخيرة', 'كاملة', 'كامله'])
            
            merged_groups.append(best)
        
        print(f'  After first pass: {len(merged_groups)} groups')
        
        # Second pass: merge groups whose Arabic-only content matches (e.g., "أخي" and "أخي abi")
        ar_groups = {}
        for item in merged_groups:
            key = arabic_only(item.get('title', ''))
            ar_groups.setdefault(key, []).append(item)
        
        merged = []
        for ar_key, entries in ar_groups.items():
            if len(entries) == 1:
                merged.append(entries[0])
            else:
                # Merge, preferring title with Latin suffix
                titles = [e.get('title', '') for e in entries]
                best_title = choose_best_title(titles)
                
                best = max(entries, key=lambda x: sum(
                    len(s.get('episodes', [])) for s in x.get('seasons', [])
                ))
                
                all_eps = {}
                for entry in entries:
                    for s in entry.get('seasons', []):
                        for ep in s.get('episodes', []):
                            ep_num = ep.get('episodeNumber') or ep.get('number', 0)
                            if ep_num and ep_num not in all_eps:
                                all_eps[ep_num] = ep
                
                sorted_eps = sorted(all_eps.values(), key=lambda e: e.get('episodeNumber', 0) or e.get('number', 0))
                
                best['title'] = best_title
                best['seasons'] = [{'season': 1, 'episodes': sorted_eps}]
                best['isComplete'] = any(
                    'الاخيرة' in e.get('title', '') or 'الأخيرة' in e.get('title', '') or 'كاملة' in e.get('title', '')
                    for e in sorted_eps
                ) or any(w in best_title for w in ['الاخيرة', 'والاخيرة', 'الأخيرة', 'والأخيرة', 'كاملة', 'كامله'])
                
                merged.append(best)
        
        print(f'  After cleanup: {len(merged)} entries')
        
        # Sort by title
        merged.sort(key=lambda x: x.get('title', ''))
        
        save_data_js(fpath, merged, var_name, label)

if __name__ == '__main__':
    main()
