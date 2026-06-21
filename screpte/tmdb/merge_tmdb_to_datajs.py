#!/usr/bin/env python3
"""
دمج بيانات TMDb (مسلسلات عربية 2020-2026) مع data.js الحالي
- تصحيح وتعبئة البوسترات الناقصة
- إضافة مسلسلات عربية جديدة غير موجودة في data.js
"""
import json, re, os, sys, unicodedata
sys.stdout.reconfigure(encoding='utf-8')

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data.js')
TMDB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def normalize_arabic(s):
    """تطبيع الاسم العربي للمقارنة"""
    s = s.strip()
    # Remove tashkeel
    s = re.sub(r'[\u064B-\u065F\u0670]', '', s)
    # Normalize alef
    s = s.replace('\u0622', '\u0627').replace('\u0623', '\u0627').replace('\u0625', '\u0627')
    # Normalize ta marbouta
    s = s.replace('\u0629', '\u0647')
    # Normalize alef maqsura
    s = s.replace('\u0649', '\u064A')
    # Remove extra spaces
    s = re.sub(r'\s+', '', s)
    return s.lower()

def load_data_js():
    """Load existing data.js"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'const contentData\s*=\s*(\[.*?\])\s*;', text, re.DOTALL)
    if not m:
        raise ValueError('Could not find contentData array in data.js')
    return json.loads(m.group(1)), text, m.group(1)

def save_data_js(items, original_text, original_json_str):
    """Save back to data.js"""
    new_json = json.dumps(items, ensure_ascii=False)
    new_text = original_text.replace(original_json_str, new_json)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print(f'Saved {len(items)} items to data.js (was {len(json.loads(original_json_str))})')

def load_tmdb_all():
    """Load all TMDb data"""
    all_series = []
    for year in range(2020, 2027):
        fp = os.path.join(TMDB_DIR, f'arabic_series_{year}.json')
        if os.path.exists(fp):
            with open(fp, 'r', encoding='utf-8') as f:
                all_series.extend(json.load(f))
    return all_series

def main():
    print('Loading data.js...')
    datajs, original_text, original_json_str = load_data_js()
    print(f'  Total items: {len(datajs)}')

    # Build normalized index of existing series (2020-2026)
    existing_normalized = {}
    for idx, item in enumerate(datajs):
        title = item.get('title', '').strip()
        year = str(item.get('year', '')).strip()
        norm = normalize_arabic(title)
        if norm:
            key = f'{norm}|{year}'
            existing_normalized.setdefault(key, []).append(idx)
            # Also store without year
            existing_normalized.setdefault(norm, []).append(idx)

    print('Loading TMDb data...')
    tmdb_series = load_tmdb_all()
    print(f'  TMDb series: {len(tmdb_series)}')

    stats = {"matched_and_updated": 0, "new": 0, "no_poster_filled": 0, "skipped": 0}
    new_entries = []

    for s in tmdb_series:
        title = s.get('title', '').strip()
        title_en = s.get('title_en', '').strip()
        year = str(s.get('year', '')).strip()
        poster = s.get('poster', '')
        norm = normalize_arabic(title)
        norm_en = normalize_arabic(title_en) if title_en else ''

        if not norm and not norm_en:
            stats["skipped"] += 1
            continue

        # Try matching by normalized Arabic title + year
        match_key = f'{norm}|{year}' if norm else ''
        matched_indices = existing_normalized.get(match_key, [])

        # Try matching by normalized English title + year
        if not matched_indices and norm_en:
            match_key_en = f'{norm_en}|{year}'
            matched_indices = existing_normalized.get(match_key_en, [])

        # Try matching by normalized Arabic title only (any year)
        if not matched_indices and norm:
            matched_indices = [i for i in existing_normalized.get(norm, [])
                              if str(datajs[i].get('year', '')).strip() == year or
                                 str(datajs[i].get('year', '')).strip() == '']

        if matched_indices:
            idx = matched_indices[0]
            item = datajs[idx]
            updated = False

            # Fill missing poster
            if not item.get('poster') and poster:
                item['poster'] = poster
                item['tmdb_poster'] = True
                stats["no_poster_filled"] += 1
                updated = True

            # Add TMDb ID
            if 'tmdb_id' not in item:
                item['tmdb_id'] = s.get('tmdb_id')
                updated = True

            # Add rating if missing
            if item.get('rating') in ('N/A', '', None) and s.get('rating'):
                item['tmdb_rating'] = s.get('rating')
                updated = True

            if updated:
                stats["matched_and_updated"] += 1
        else:
            # New series - add to data.js
            new_item = {
                "title": title,
                "title_en": title_en,
                "year": year,
                "rating": "N/A",
                "type": "مسلسل عربي",
                "description": s.get('arabic_overview') or s.get('overview', ''),
                "poster": poster,
                "tmdb_id": s.get('tmdb_id'),
                "tmdb_rating": s.get('rating'),
                "genres": s.get('genres', []),
                "networks": s.get('networks', []),
                "origin_country": s.get('origin_country', []),
                "seasons_count": s.get('seasons_count', 0),
                "episodes_count": s.get('episodes_count', 0),
                "status": s.get('status', ''),
                "first_air_date": s.get('first_air_date', ''),
                "contentType": "series",
            }
            datajs.append(new_item)
            new_entries.append(title)
            stats["new"] += 1

    print('\n=== Merge Results ===')
    print(f'  Matched & updated: {stats["matched_and_updated"]}')
    print(f'  Missing posters filled: {stats["no_poster_filled"]}')
    print(f'  New series added: {stats["new"]}')
    print(f'  Skipped (no name): {stats["skipped"]}')

    if new_entries:
        print(f'\nNew series added (sample):')
        for t in new_entries[:20]:
            print(f'  + {t}')
        if len(new_entries) > 20:
            print(f'  ... and {len(new_entries) - 20} more')

    # Save
    save_data_js(datajs, original_text, original_json_str)
    print('\nDone!')

if __name__ == '__main__':
    main()
