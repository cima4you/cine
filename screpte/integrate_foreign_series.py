#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت دمج نتائج المسلسلات الأجنبية في الموقع
------------------
الاستعمال:
  python scripts/integrate_foreign_series.py
"""
import os, sys, shutil

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1, closefd=False)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1, closefd=False)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, 'scripts', 'tuktukhd', 'data_foreign_series.js')
SPLIT_DIR = os.path.join(BASE, 'split')
RACHID_DIR = os.path.join(BASE, 'RACHID')
TEST_DIR = os.path.join(BASE, 'test')

# ===== 1. Copy file =====
print("[1/7] Copy data_foreign_series.js -> split/data-foreign-series.js")
shutil.copy2(SRC, os.path.join(SPLIT_DIR, 'data-foreign-series.js'))
print("      OK")

# ===== 2. Update data-loader.js =====
print("[2/7] Update split/data-loader.js")
lp = os.path.join(SPLIT_DIR, 'data-loader.js')
with open(lp, 'r', encoding='utf-8') as f:
    loader = f.read()
if 'cd_foreign_series' not in loader:
    loader = loader.replace(
        'const contentData = [].concat(',
        'const contentData = [].concat(cd_foreign_series, '
    )
    with open(lp, 'w', encoding='utf-8') as f:
        f.write(loader)
    print("      OK")
else:
    print("      Already present")

# ===== 3. Patch HTML =====
def patch_html(html):
    """Add foreign-series category + filter logic to HTML string"""
    # 3a. CATEGORIES entry after 'foreign'
    old_cat = "{ id: 'foreign', label: '🌍 أفلام أجنبية', type: 'أجنبي', contentType: 'movie', limit: 100, clr: 'blue' },"
    new_cat = old_cat + "\n    { id: 'foreign-series', label: '🌍 مسلسلات أجنبية', type: 'أجنبي', contentType: 'series', limit: 100, clr: 'blue' },"
    if 'foreign-series' not in html:
        html = html.replace(old_cat, new_cat)
        print("      + CATEGORIES entry")
    else:
        print("      ~ CATEGORIES entry already present")

    def insert_after(haystack, needle, insertion):
        """Insert string after the first occurrence of needle"""
        if insertion not in haystack:
            idx = haystack.find(needle)
            if idx >= 0:
                return haystack[:idx + len(needle)] + insertion + haystack[idx + len(needle):]
        return haystack

    # 3b. updateYearOptions: add foreign-series filter after asian-series-ongoing
    needle_uy = "else if (catVal === 'asian-series-ongoing' && (it !== 'أسيوي' || ct !== 'series' || m.isComplete)) skip = true;"
    insert_uy = "\n                    else if (catVal === 'foreign-series' && (it !== 'أجنبي' || ct !== 'series')) skip = true;"
    html = insert_after(html, needle_uy, insert_uy)
    if insert_uy in html:
        print("      + updateYearOptions filter")

    # 3c. applyFilters: add foreign-series filter after asian-series-ongoing
    needle_af = "else if (catVal === 'asian-series-ongoing' && (it !== 'أسيوي' || ct !== 'series' || item.isComplete)) return false;"
    insert_af = "\n                    else if (catVal === 'foreign-series' && (it !== 'أجنبي' || ct !== 'series')) return false;"
    html = insert_after(html, needle_af, insert_af)
    if insert_af in html:
        print("      + applyFilters filter")

    # 3d. catLabels
    needle_cl = "'anime-series':'مسلسلات أنمي',"
    insert_cl = " 'foreign-series':'مسلسلات أجنبية',"
    html = insert_after(html, needle_cl, insert_cl)
    if insert_cl in html:
        print("      + catLabels entry")

    # 3e. Others exclusion list (updateYearOptions version)
    needle_oth_uy = "'وثائقي'].includes(it)) skip = true;"
    if needle_oth_uy in html and "'foreign-series'" not in html[:html.find(needle_oth_uy)]:
        html = html.replace(needle_oth_uy, "'وثائقي','foreign-series'].includes(it)) skip = true;")
        print("      + others exclusion (updateYearOptions)")

    # 3f. Others exclusion (applyFilters version)
    needle_oth_af = "'وثائقي'].includes(it)) return false;"
    if needle_oth_af in html and "'foreign-series'" not in html[:html.find(needle_oth_af)]:
        html = html.replace(needle_oth_af, "'وثائقي','foreign-series'].includes(it)) return false;")
        print("      + others exclusion (applyFilters)")

    # 3g. Add foreign-series to turkish-scroll class
    needle_scr = "cat.id === 'arabic-series' || cat.id === 'turkish-completed' || cat.id === 'turkish-ongoing' || cat.id === 'asian-series-completed' || cat.id === 'asian-series-ongoing' || cat.id === 'anime-series'"
    if needle_scr in html and "'foreign-series'" not in html:
        html = html.replace(needle_scr,
            "cat.id === 'arabic-series' || cat.id === 'foreign-series' || cat.id === 'turkish-completed' || cat.id === 'turkish-ongoing' || cat.id === 'asian-series-completed' || cat.id === 'asian-series-ongoing' || cat.id === 'anime-series'")
        print("      + turkish-scroll class")

    return html

print("[3/7] Update split/index.html")
p = os.path.join(SPLIT_DIR, 'index.html')
with open(p, 'r', encoding='utf-8') as f:
    h = f.read()
h = patch_html(h)
# Add script tag
if 'data-foreign-series.js' not in h:
    h = h.replace('<script src="data-foreign.js"></script>',
                  '<script src="data-foreign.js"></script>\n    <script src="data-foreign-series.js"></script>')
    print("      + script tag")
with open(p, 'w', encoding='utf-8') as f:
    f.write(h)
print("      OK")

print("[4/7] Update RACHID/test2.html")
p = os.path.join(RACHID_DIR, 'test2.html')
with open(p, 'r', encoding='utf-8') as f:
    h = f.read()
h = patch_html(h)
with open(p, 'w', encoding='utf-8') as f:
    f.write(h)
print("      OK")

print("[5/7] Update test/test2.html")
p = os.path.join(TEST_DIR, 'test2.html')
with open(p, 'r', encoding='utf-8') as f:
    h = f.read()
h = patch_html(h)
with open(p, 'w', encoding='utf-8') as f:
    f.write(h)
print("      OK")

# ===== 6+7. Append data to data.js =====
def append_foreign_series(data_js_path):
    print(f"      Reading {os.path.basename(data_js_path)} ...")
    with open(data_js_path, 'r', encoding='utf-8') as f:
        d = f.read()
    if '// foreign series appended' in d or 'cd_foreign_series' in d:
        print("      Already present, skipping")
        return
    with open(SRC, 'r', encoding='utf-8') as f:
        src = f.read()
    # extract items between [ and ]
    start = src.index('[')
    end = src.rindex(']')
    items = src[start+1:end].strip()
    if items.startswith('\n'):
        items = items[1:]
    # find last ]; or ] \n ;
    pos = d.rfind('];')
    if pos < 0:
        # try finding last ] followed by optional newline and ;
        pos = d.rfind(']')
        if pos < 0:
            print("      Error: no ] found")
            return
        # check if after the ] there's optional whitespace/then ;
        rest = d[pos+1:].strip()
        if rest == ';':
            pass  # pos already points to the right ]
        else:
            print("      Error: unexpected trailing content after ]")
            return
    d = d[:pos].rstrip() + ',\n' + items + '\n' + d[pos:]
    d = d.replace('const contentData = [', '// foreign series appended\nconst contentData = [', 1)
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write(d)
    print("      OK")

print("[6/7] Append to RACHID/data.js")
append_foreign_series(os.path.join(RACHID_DIR, 'data.js'))

print("[7/7] Append to test/data.js")
append_foreign_series(os.path.join(TEST_DIR, 'data.js'))

print("\nDone! 320 foreign series added to the site.")
print("Refresh RACHID/test2.html, test/test2.html, or split/index.html")
