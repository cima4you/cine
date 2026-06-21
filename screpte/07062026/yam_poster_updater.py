#!/usr/bin/env python3
"""
سكربت تحديث صور المسلسلات العربية من yam.ahwaktv.net
------------------------------
يقرأ جميع المسلسلات العربية من data.js، 
ويبحث عن كل مسلسل على yam.ahwaktv.net (عن طريق البحث)،
ويستخرج رابط الصورة من صفحة المشاهدة (og:image),
ويحدث الرابط في data.js.
"""
import urllib.request, urllib.parse, json, re, os, sys, time, random
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
PROGRESS_PATH = os.path.join(SCRIPT_DIR, '_yam_poster_progress.json')
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def log(msg):
    print(msg, flush=True)

def fetch(url, referer=None):
    headers = {'User-Agent': USER_AGENT}
    if referer:
        headers['Referer'] = referer
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=20)
        return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        log(f'    ! خطأ في جلب {url}: {e}')
        return None

def normalize(t):
    t = re.sub(r'[\u064B-\u0652]', '', t)
    t = re.sub(r'\s+', '', t)
    return t.strip().lower()

def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def search_series(title, year):
    """البحث عن مسلسل على yam.ahwaktv.net وإرجاع قائمة بالنتائج (العنوان, الرابط, الصورة)."""
    results = []
    search_url = f'https://yam.ahwaktv.net/search.php?keywords={urllib.parse.quote(title)}'
    html = fetch(search_url, 'https://yam.ahwaktv.net/')
    if not html:
        return results
    
    # استخراج نتائج البحث
    items = re.findall(r'<li class="col-xs-6 col-sm-4 col-md-3">(.*?)</li>', html, re.DOTALL)
    seen_links = set()
    for item_html in items:
        link_m = re.search(r'href="([^"]*)"', item_html)
        link = link_m.group(1) if link_m else ''
        if not link or link.startswith('#') or link in seen_links:
            continue
        seen_links.add(link)
        
        title_m = re.search(r'alt="([^"]*)"', item_html)
        item_title = title_m.group(1).strip() if title_m else ''
        
        poster_m = re.search(r'<img[^>]*src="([^"]*)"', item_html)
        poster = poster_m.group(1) if poster_m else ''
        
        if item_title:
            results.append({'title': item_title, 'link': link, 'poster': poster})
    
    return results

def extract_poster_from_watch(watch_url):
    """الدخول إلى صفحة المشاهدة واستخراج og:image."""
    html = fetch(watch_url, 'https://yam.ahwaktv.net/')
    if not html:
        return None
    
    # الطريقة 1: og:image
    m = re.search(r'og:image["\']\s+content=["\']([^"\']*)["\']', html)
    if m:
        img = m.group(1)
        if img and 'echo-lzld' not in img:
            return img
    
    # الطريقة 2: pm-series-brief
    m = re.search(r'<div class="pm-series-brief">(.*?)</div>', html, re.DOTALL)
    if m:
        brief = m.group(1)
        img_m = re.search(r'<img[^>]*src="([^"]*)"', brief)
        if img_m:
            img = img_m.group(1)
            if img and 'echo-lzld' not in img:
                return img
    
    return None

def get_series_vid_from_category(title, year):
    """محاولة إيجاد VID للمسلسل من خلال صفحة التصنيف."""
    # تحديد التصنيف المناسب حسب السنة
    year_cats = {
        '2022': 'moslslat-ramdan-2022',
        '2023': 'moslslat-ramdan-2023',
        '2024': 'moslslat-ramadan-2024',
        '2025': ['moslslat-ramdan-2025', 'ramdan-series-2025'],
        '2026': ['ramdan-series-2026', 'moslslat-ramdan-2025'],
    }
    
    cats = year_cats.get(year, [])
    if isinstance(cats, str):
        cats = [cats]
    
    title_normalized = normalize(title)
    title_clean = re.sub(r'^(مسلسل|فلم|فيلم)\s*', '', title).strip()
    title_clean_normalized = normalize(title_clean)
    
    for cat in cats:
        for page in range(1, 4):  # أول 3 صفحات فقط
            url = f'https://yam.ahwaktv.net/category.php?cat={cat}&page={page}'
            html = fetch(url, 'https://yam.ahwaktv.net/')
            if not html:
                continue
            
            items = re.findall(r'<li class="col-xs-6 col-sm-4 col-md-3">(.*?)</li>', html, re.DOTALL)
            for item_html in items:
                link_m = re.search(r'href="([^"]*watch[^"]*)"', item_html)
                if not link_m:
                    continue
                link = link_m.group(1)
                
                title_m = re.search(r'alt="([^"]*)"', item_html)
                if not title_m:
                    continue
                item_title = title_m.group(1).strip()
                
                # تنظيف عنوان النتيجة (إزالة "مسلسل" و "الحلقة X")
                item_clean = re.sub(r'^(مسلسل|فلم|فيلم)\s*', '', item_title)
                item_clean = re.sub(r'\s*الحلقة\s*\d+\s*.*$', '', item_clean).strip()
                
                # مقارنة العناوين
                item_norm = normalize(item_clean)
                if item_norm == title_normalized or item_norm == title_clean_normalized:
                    return link
                
                # فحص التشابه
                sim = similarity(title_clean, item_clean)
                if sim > 0.85:
                    return link
    
    return None

def main():
    log('=' * 60)
    log('سكربت تحديث صور المسلسلات العربية من yam.ahwaktv.net')
    log('=' * 60)
    
    # تحميل data.js
    log('\n1. جاري تحميل data.js...')
    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    arr_start = content.index('[')
    arr_end = content.rindex(']') + 1
    data = json.loads(content[arr_start:arr_end])
    prefix = content[:arr_start]
    suffix = content[arr_end:]
    log(f'   {len(data)} عنصر في data.js')
    
    # تحديد المسلسلات العربية
    arabic_series = []
    for i, item in enumerate(data):
        ct = item.get('contentType', '')
        t = (item.get('type') or '').strip()
        if ct == 'series' and (t == 'عربي' or t.startswith('رمضان')):
            arabic_series.append((i, item))
    
    log(f'   {len(arabic_series)} مسلسل عربي')
    
    # استثناء المسلسلات التي لديها صور من elcinema (هي الأفضل)
    to_check = []
    for idx, item in arabic_series:
        p = item.get('poster', '') or ''
        if not p or 'elcinema' not in p:
            to_check.append((idx, item))
    
    log(f'   {len(to_check)} مسلسل يحتاج تحديث الصورة (بدون elcinema)')
    
    if not to_check:
        log('\n✅ جميع المسلسلات العربية لديها صور من elcinema. لا حاجة للتحديث.')
        return
    
    # استئناف من التقدم المحفوظ
    done_titles = set()
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
            done_titles = set(json.load(f))
        log(f'   استئناف: {len(done_titles)} مسلسل تم معالجته سابقاً')
    
    updated = 0
    skipped = 0
    errors = 0
    
    log('\n2. جاري تحديث الصور...')
    
    for idx, item in to_check:
        title = item.get('title', '').strip()
        year = str(item.get('year', '') or '')
        
        if title in done_titles:
            skipped += 1
            continue
        
        log(f'\n   🔍 {title} ({year})')
        
        # الخطوة 1: البحث عن المسلسل
        vid_url = get_series_vid_from_category(title, year)
        
        if vid_url:
            # تحويل الرابط النسبي إلى مطلق
            if vid_url.startswith('/'):
                vid_url = 'https://yam.ahwaktv.net' + vid_url
            elif vid_url.startswith('?'):
                vid_url = 'https://yam.ahwaktv.net/watch.php' + vid_url
            
            log(f'      -> تم إيجاد الرابط: {vid_url[:80]}')
            
            # الخطوة 2: استخراج الصورة من صفحة المشاهدة
            poster = extract_poster_from_watch(vid_url)
            
            if poster and 'echo-lzld' not in poster:
                log(f'      -> صورة جديدة: {poster[:80]}')
                data[idx]['poster'] = poster
                updated += 1
            else:
                log(f'      -> لم يتم العثور على صورة صالحة')
                errors += 1
        else:
            log(f'      -> لم يتم العثور على المسلسل في yam.ahwaktv.net')
            errors += 1
        
        # حفظ التقدم
        done_titles.add(title)
        with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
            json.dump(list(done_titles), f, ensure_ascii=False)
        
        # حفظ التحديثات كل 10 مسلسلات
        if updated % 10 == 0 and updated > 0:
            save_data_js(data, prefix, suffix)
        
        # انتظار مهذب
        time.sleep(random.uniform(1.5, 3))
    
    # الحفظ النهائي
    if updated > 0:
        save_data_js(data, prefix, suffix)
    
    log('\n' + '=' * 60)
    log(f'تم الانتهاء:')
    log(f'  - تم التحديث: {updated}')
    log(f'  - تم التخطي: {skipped}')
    log(f'  - أخطاء: {errors}')
    log(f'  - إجمالي المسلسلات العربية: {len(arabic_series)}')
    log('=' * 60)

def save_data_js(data, prefix, suffix):
    json_str = json.dumps(data, ensure_ascii=False)
    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)
    size_mb = os.path.getsize(DATA_JS_PATH) / (1024 * 1024)
    log(f'\n   💾 تم الحفظ: {len(data)} عنصر, {size_mb:.1f} MB')

if __name__ == '__main__':
    main()
