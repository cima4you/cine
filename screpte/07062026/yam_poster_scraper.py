#!/usr/bin/env python3
"""
استخراج صور المسلسلات العربية من yam.ahwaktv.net
==============================================
1. يسحب جميع صفحات التصنيفات (ramdan 2022-2026)
2. يستخرج روابط الصور من data-echo
3. ينظف العناوين (إزالة "مسلسل" و "الحلقة X")
4. يحفظ النتائج في ملف JSON
5. يدمج الصور في data.js
"""
import urllib.request, json, re, os, sys, time, random
from collections import OrderedDict
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'scripts', 'yam_posters.json')
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

CATEGORIES = [
    ('moslslat-ramdan-2022', '2022'),
    ('moslslat-ramdan-2023', '2023'),
    ('moslslat-ramadan-2024', '2024'),
    ('moslslat-ramdan-2025', '2025'),
    ('ramdan-series-2026', '2026'),
]

def log(msg):
    print(msg, flush=True)

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        resp = urllib.request.urlopen(req, timeout=20)
        return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        log(f'  ⚠ خطأ: {e}')
        return None

def extract_items(html):
    """استخراج قائمة العناصر من HTML صفحة التصنيف"""
    items = re.findall(r'<li class="col-xs-6 col-sm-4 col-md-3">(.*?)</li>', html, re.DOTALL)
    result = []
    for item_html in items:
        title_m = re.search(r'alt="([^"]*)"', item_html)
        echo_m = re.search(r'data-echo\s*=\s*["\']([^"\']*)["\']', item_html)
        link_m = re.search(r'href="([^"]*watch[^"]*)"', item_html)
        if title_m and echo_m:
            result.append({
                'title': title_m.group(1).strip(),
                'poster': echo_m.group(1).strip(),
                'link': link_m.group(1) if link_m else '',
            })
    return result

def clean_series_title(episode_title):
    """تنظيف عنوان الحلقة للحصول على اسم المسلسل"""
    t = episode_title.strip()
    # إزالة "مسلسل" من البداية
    t = re.sub(r'^مسلسل\s*', '', t)
    # إزالة "الحلقة X" وما بعدها
    t = re.sub(r'\s*الحلقة\s*\d+\s*.*$', '', t)
    # إزالة أرقام الجودة مثل HD, كاملة
    t = re.sub(r'\s*(HD|720P|1080P|كامله|كاملة|والاخيرة)\s*$', '', t, flags=re.IGNORECASE)
    return t.strip()

def normalize(t):
    t = re.sub(r'[\u064B-\u0652]', '', t)
    t = re.sub(r'\s+', '', t)
    return t.strip().lower()

def scrape_category(cat_slug, year_label):
    """سحب جميع صفحات تصنيف معين"""
    all_items = []
    page = 1
    max_page = None
    
    while True:
        url = f'https://yam.ahwaktv.net/category.php?cat={cat_slug}&page={page}&order=DESC'
        log(f'  📄 الصفحة {page}...')
        html = fetch(url)
        if not html:
            break
        
        items = extract_items(html)
        if not items:
            log(f'     لا توجد عناصر - انتهى')
            break
        
        log(f'     -> {len(items)} عنصر')
        all_items.extend(items)
        
        # تحديد آخر صفحة
        if max_page is None:
            pages = re.findall(r'page=(\d+)', html)
            if pages:
                max_page = max(int(p) for p in pages if p.isdigit())
                log(f'     -> آخر صفحة: {max_page}')
        
        if max_page and page >= max_page:
            break
        
        page += 1
        time.sleep(random.uniform(0.5, 1.5))
    
    return all_items

def build_series_map(items):
    """بناء قاموس المسلسلات {العنوان_النظيف: poster_url}
       كل مسلسل يأخذ البوستر الخاص بأول حلقة."""
    series_map = OrderedDict()
    for item in items:
        clean_title = clean_series_title(item['title'])
        norm = normalize(clean_title)
        if norm and norm not in series_map:
            series_map[norm] = {
                'title': clean_title,
                'poster': item['poster'],
                'link': item['link'],
                'original': item['title'],
            }
    return series_map

def save_results(series_map, output_path):
    """حفظ النتائج في ملف JSON"""
    output = []
    for norm, info in series_map.items():
        output.append(info)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log(f'  💾 تم الحفظ: {len(output)} مسلسل -> {output_path}')
    return output

def merge_to_datajs(series_list):
    """دمج الصور في data.js مع مطابقة العناوين"""
    log('\n' + '=' * 60)
    log('دمج الصور في data.js')
    log('=' * 60)
    
    # تحميل data.js
    log('\n📂 تحميل data.js...')
    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    arr_start = content.index('[')
    arr_end = content.rindex(']') + 1
    data = json.loads(content[arr_start:arr_end])
    prefix = content[:arr_start]
    suffix = content[arr_end:]
    log(f'   {len(data)} عنصر')
    
    # بناء قاموس للمسلسلات من yam
    yam_map = {}
    for s in series_list:
        norm = normalize(s['title'])
        yam_map[norm] = s['poster']
    
    # البحث عن المسلسلات العربية في data.js
    updated = 0
    skipped_elcinema = 0
    not_found = []
    already_yam = 0
    already_other = 0
    
    for idx, item in enumerate(data):
        ct = item.get('contentType', '')
        t = (item.get('type') or '').strip()
        if ct != 'series' or not (t == 'عربي' or t.startswith('رمضان')):
            continue
        
        title = item.get('title', '').strip()
        current_poster = item.get('poster', '') or ''
        norm = normalize(title)
        
        # مطابقة تامة
        if norm in yam_map:
            new_poster = yam_map[norm]
            if 'elcinema' in current_poster:
                skipped_elcinema += 1  # elcinema أفضل - لا نستبدلها
                continue
            if current_poster == new_poster:
                already_yam += 1
                continue
            data[idx]['poster'] = new_poster
            updated += 1
            log(f'  ✅ {title}')
            continue
        
        # مطابقة تقريبية
        best_match = None
        best_score = 0
        for yam_norm, yam_poster in yam_map.items():
            score = SequenceMatcher(None, norm, yam_norm).ratio()
            if score > best_score and score > 0.7:
                best_score = score
                best_match = yam_norm
        
        if best_match and best_score > 0.75:
            new_poster = yam_map[best_match]
            if 'elcinema' in current_poster:
                skipped_elcinema += 1
                continue
            data[idx]['poster'] = new_poster
            updated += 1
            log(f'  🔀 {title} <- {best_match} ({best_score:.2f})')
        else:
            not_found.append(title)
    
    log(f'\n{"=" * 60}')
    log(f'النتائج:')
    log(f'  ✅ تم التحديث: {updated}')
    log(f'  ⏭ تم التخطي (elcinema أفضل): {skipped_elcinema}')
    log(f'  ♻ موجود مسبقاً: {already_yam}')
    log(f'  ❌ غير موجود في yam: {len(not_found)}')
    if not_found:
        log('\n  أول 10 غير موجودة:')
        for t in not_found[:10]:
            log(f'    - {t}')
    
    if updated > 0:
        json_str = json.dumps(data, ensure_ascii=False)
        with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
            f.write(prefix + json_str + suffix)
        size_mb = os.path.getsize(DATA_JS_PATH) / (1024 * 1024)
        log(f'\n  💾 تم الحفظ: {len(data)} عنصر, {size_mb:.1f} MB')
    
    return updated

def main():
    log('=' * 60)
    log('استخراج صور المسلسلات العربية من yam.ahwaktv.net')
    log('=' * 60)
    
    all_series_map = OrderedDict()
    
    # سحب كل التصنيفات
    for cat_slug, year_label in CATEGORIES:
        log(f'\n📁 تصنيف: {cat_slug} ({year_label})')
        items = scrape_category(cat_slug, year_label)
        log(f'   إجمالي العناصر: {len(items)}')
        
        series_map = build_series_map(items)
        log(f'   مسلسلات فريدة: {len(series_map)}')
        
        for norm, info in series_map.items():
            if norm not in all_series_map:
                all_series_map[norm] = info
        
        log(f'   الإجمالي حتى الآن: {len(all_series_map)}')
        time.sleep(random.uniform(1, 2))
    
    log(f'\n{"=" * 60}')
    log(f'✅ إجمالي المسلسلات الفريدة: {len(all_series_map)}')
    
    # حفظ النتائج
    series_list = save_results(all_series_map, OUTPUT_PATH)
    
    # دمج في data.js
    merge_to_datajs(series_list)
    
    log(f'\n{"=" * 60}')
    log('انتهى ✅')
    log('=' * 60)

if __name__ == '__main__':
    main()
