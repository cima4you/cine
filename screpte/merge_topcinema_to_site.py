#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
دمج بيانات TopCinema (أفلام أجنبية) مع ملفات الموقع بدون تكرار الأسماء.
يستخدم نهجًا فعالاً للذاكرة: لا يقرأ الملفات الكاملة في الذاكرة كـ JSON.
"""
import json, re, os, shutil, time, sys

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = __import__('io').TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\Users\DT01\Desktop\rachid-site'
TOP_JSON = os.path.join(BASE, r'scripts\topcinema\data\topcinema_full.json')

FILES = [
    os.path.join(BASE, r'test\data.js'),
    os.path.join(BASE, r'RACHID\data.js'),
    os.path.join(BASE, r'split\data-foreign.js'),
]

def load_topcinema():
    with open(TOP_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def transform_movie(m):
    # Split genres
    genre_raw = m.get('genre', '') or ''
    categories = [g.strip() for g in re.split(r'[،,/-]', genre_raw) if g.strip()]
    servers = m.get('servers', [])
    for s in servers:
        if 'isDefault' not in s:
            s['isDefault'] = len(servers) == 1
    return {
        'title': m.get('title', ''),
        'year': str(m.get('year', '') or ''),
        'rating': '',
        'duration': '',
        'quality': m.get('quality', '') or '',
        'type': 'أجنبي',
        'description': m.get('description', '') or '',
        'cast': m.get('cast', []),
        'categories': categories,
        'poster': m.get('poster', '') or '',
        'servers': servers,
        'downloadServers': m.get('downloadServers', []),
        'trial': '',
        'contentType': 'movie',
        'isComplete': False,
    }

def extract_titles(text):
    """Extract all titles from a data.js file efficiently using regex."""
    titles = set()
    # Match "title":"..." patterns in the JSON
    for m in re.finditer(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', text):
        titles.add(m.group(1))
    return titles

def find_array_bounds(text):
    """Find the position of the opening [ and closing ]; of the main array."""
    m = re.search(r'(const\s+\w+\s*=\s*)\[', text)
    if not m:
        raise ValueError('Cannot find array declaration')
    start = m.end()  # position right after [
    # Now find matching closing ]
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        i += 1
    end = i - 1  # position of the closing ]
    return start, end, text[:m.start()], text[m.start():m.end()-1], text[end+1:]

def merge_into_file(path, new_movies):
    """Merge new movies into a data.js file without full JSON parsing."""
    if not os.path.exists(path):
        print(f'  ❌ غير موجود')
        return 0

    print(f'  قراءة {os.path.basename(path)}...', end=' ', flush=True)
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f'{len(text)//1024//1024}MB')

    # Extract existing titles
    existing_titles = extract_titles(text)
    print(f'  العناوين الموجودة: {len(existing_titles)}')

    # Find insertion point
    start, end, header, decl, footer = find_array_bounds(text)

    # Filter new movies by title
    to_add = []
    for m in new_movies:
        t = m.get('title', '')
        if t and t not in existing_titles:
            to_add.append(m)

    if not to_add:
        print(f'  ✏️  لا توجد أفلام جديدة للإضافة')
        return 0

    # Generate JSON for new movies
    new_json = json.dumps(to_add, ensure_ascii=False)
    # Remove outer [ ] 
    new_json = new_json[1:-1]

    # Get existing array content
    existing_content = text[start:end].strip()

    # Build new file:
    # If array is empty, just put the new items
    if not existing_content:
        new_array = '[\n' + new_json + '\n'
    else:
        new_array = '[' + new_json + ',\n' + existing_content

    new_text = header + decl + new_array + footer

    # Write temp file then replace
    tmp = path + '.merge_tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(new_text)
    os.replace(tmp, path)

    print(f'  ✅ +{len(to_add)} فيلم (الإجمالي الجديد: {len(existing_titles) + len(to_add)})')
    return len(to_add)

def main():
    start_time = time.time()
    print('=== دمج أفلام TopCinema مع ملفات الموقع ===\n')

    raw = load_topcinema()
    print(f'📥 TopCinema: {len(raw)} فيلم')
    new_movies = [transform_movie(m) for m in raw]
    print(f'🔄 تحويل: {len(new_movies)} فيلم\n')

    total_added = 0
    for fp in FILES:
        print(f'📂 {fp}')
        bak = fp + '.bak'
        if not os.path.exists(bak):
            shutil.copy2(fp, bak)
        added = merge_into_file(fp, new_movies)
        total_added += added
        print()

    elapsed = time.time() - start_time
    print(f'✅ الإجمالي: +{total_added} فيلم (بدون تكرار) — {elapsed:.1f} ثانية')

if __name__ == '__main__':
    main()
