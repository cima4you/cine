#!/usr/bin/env python3
"""
سكربت سحب مسلسلات الأنمي من رويال دراما
الاستعمال:
  python scripts/royal/scrape_royal_anime.py --start 1 --end 10 --workers 4
  python scripts/royal/scrape_royal_anime.py --start 1 --end 10 --phase listing
  python scripts/royal/scrape_royal_anime.py --start 1 --end 10 --resume
  python scripts/royal/scrape_royal_anime.py --convert  # تحويل النتائج لصيغة data-anime-series.js
"""
import os, sys, re, json, time, argparse, copy, glob
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = __import__('io').TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import requests

BASE = 'https://w9.royal-drama.com'
CAT = 'musalsalat-animiee-2025'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}
SES = requests.Session()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def p(text):
    try: print(text, flush=True)
    except: print(repr(text), flush=True)

def fetch(url, **kwargs):
    for attempt in range(5):
        try:
            r = SES.get(url, headers=HEADERS, timeout=30, **kwargs)
            r.raise_for_status()
            return r
        except Exception as e:
            if '429' in str(e) and attempt < 4:
                time.sleep(3 * (attempt + 1))
                continue
            if attempt < 4:
                time.sleep(2)
                continue
            raise

def fetch_text(url, **kwargs):
    return fetch(url, **kwargs).text

def save_json(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def load_json(path):
    if not os.path.exists(path):
        return [] if 'listing' in path else {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ===== المرحلة 1: القائمة =====
def extract_series_name(title):
    """استخراج اسم المسلسل من عنوان الحلقة"""
    if not title: return ''
    clean = re.sub(r'^(?:مسلسل|برنامج|فيلم|movie|series|انمي)\s+', '', title, flags=re.IGNORECASE).strip()
    # "انمي XXX الحلقة 11" -> "XXX"
    m = re.match(r'(.*?)\s+الحلقة\s+\d+', clean)
    if m:
        name = m.group(1).strip()
        name = re.sub(r'\s+(?:مترجم|مدبلج|HD|FHD|SD|جميع الحلقات|جميع.*)$', '', name, flags=re.IGNORECASE).strip()
        return name.strip()
    m = re.match(r'(.*?)\s+حلقة\s+\d+', clean)
    if m:
        name = m.group(1).strip()
        name = re.sub(r'\s+(?:مترجم|HD|FHD|SD).*$', '', name, flags=re.IGNORECASE).strip()
        return name.strip()
    m = re.match(r'(.*?)\s+(?:Episode|Ep\.?)\s+\d+', clean, re.IGNORECASE)
    if m: return m.group(1).strip()
    # لا يوجد رقم حلقة -> هذا قد يكون اسم المسلسل نفسه
    clean = re.sub(r'\s+(?:مترجم|مدبلج|HD|FHD|SD|-\s+).*$', '', clean, flags=re.IGNORECASE).strip()
    return clean

def extract_ep_num(title):
    if not title: return 0
    # تجاهل روابط التنقل
    if 'السابقة' in title or 'التالية' in title: return 0
    m = re.search(r'الحلقة\s+(\d+)', title)
    if m: return int(m.group(1))
    m = re.search(r'حلقة\s+(\d+)', title)
    if m: return int(m.group(1))
    m = re.search(r'(?:Episode|Ep\.?)\s+(\d+)', title, re.IGNORECASE)
    if m: return int(m.group(1))
    # محاولة استخراج رقم من نهاية النص
    m = re.search(r'(\d+)\s*$', title)
    if m: return int(m.group(1))
    return 0

def listing_page(page):
    url = f'{BASE}/category3.php?cat={CAT}&page={page}&order=DESC'
    html = fetch_text(url)
    items = []
    cards = re.findall(r'<li class="col-xs-6 col-sm-4 col-md-3">(.*?)</li>', html, re.DOTALL)
    for card in cards:
        try:
            links = re.findall(r'<a\s+href="(https?://[^"]*watch\.php\?vid=([a-f0-9]+))"[^>]*>', card)
            if not links: continue
            ep_url = links[0][0]
            vid = links[0][1]
            title_links = re.findall(r'<a\s+href="https?://[^"]*watch\.php\?vid=[a-f0-9]+"[^>]*\s+title="([^"]+)"', card)
            title = title_links[0] if title_links else ''
            dur = re.search(r'<span class="pm-label-duration">([^<]+)</span>', card)
            img = re.search(r'<img[^>]+src="([^"]+)"[^>]*>', card)
            ep_span = re.search(r'<span class="ep">الحلقة\s*(\d+)</span>', card)
            ep_num = int(ep_span.group(1)) if ep_span else extract_ep_num(title)
            sname = extract_series_name(title)
            items.append({
                'vid': vid, 'url': ep_url, 'title': title,
                'duration': dur.group(1).strip() if dur else '',
                'thumbnail': img.group(1) if img else '',
                'episodeNumber': ep_num, 'seriesName': sname,
            })
        except:
            continue
    return items

def run_listing(start, end, workers, resume=False):
    path = os.path.join(DATA_DIR, 'results_listing.json')
    all_items = load_json(path) if resume else []
    existing = {it['vid'] for it in all_items}
    pages = list(range(start, end + 1))
    with ThreadPoolExecutor(max_workers=min(workers, 8)) as ex:
        futs = {ex.submit(listing_page, p): p for p in pages}
        for f in as_completed(futs):
            p_ = futs[f]
            try:
                new = f.result()
                cnt = 0
                for it in new:
                    if it['vid'] not in existing:
                        all_items.append(it)
                        existing.add(it['vid'])
                        cnt += 1
                p(f'  ✅ صفحة {p_}: +{cnt} ({len(all_items)})')
            except Exception as e:
                p(f'  ❌ صفحة {p_}: {e}')
    save_json(path, all_items)
    p(f'📁 القائمة: {len(all_items)} عنصر')
    return all_items

def group_series(items):
    sm = OrderedDict()
    for it in items:
        name = it.get('seriesName', '')
        if not name: continue
        if name not in sm:
            sm[name] = {'seriesName': name, 'title': name, 'episodes': [], '_vids': set()}
        if it['vid'] not in sm[name]['_vids']:
            sm[name]['episodes'].append({
                'number': it['episodeNumber'], 'vid': it['vid'], 'url': it['url'],
                'title': it['title'], 'duration': it['duration'], 'thumbnail': it['thumbnail'],
            })
            sm[name]['_vids'].add(it['vid'])
    for d in sm.values():
        d['episodes'].sort(key=lambda e: e['number'])
        d.pop('_vids', None)
    return list(sm.values())

# ===== المرحلة 2: التفاصيل =====
def watch_detail(vid):
    url = f'{BASE}/watch.php?vid={vid}'
    html = fetch_text(url)
    s = {}
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html)
    if h1: s['title'] = h1.group(1).strip()
    img = re.search(r'<div class="pm-series-brief">.*?<img[^>]+src="([^"]+)"', html, re.DOTALL)
    if img: s['poster'] = img.group(1)
    desc = re.search(r'<div itemprop="description">\s*<p>(.*?)</p>', html, re.DOTALL)
    if desc: s['description'] = desc.group(1).strip()
    if not desc:
        desc = re.search(r'<div class="pm-series-description">.*?<p>(.*?)</p>', html, re.DOTALL)
        if desc: s['description'] = desc.group(1).strip()
    cats = re.findall(r'<dt>الاقسام</dt>\s*<dd>(.*?)</dd>', html, re.DOTALL)
    if cats:
        cl = re.findall(r'<a[^>]*>(.*?)</a>', cats[0])
        if cl: s['categories'] = [c.strip() for c in cl]
    # تنظيف العنوان: إزالة "انمي" prefix وأرقام الحلقات
    if s.get('title'):
        s['title'] = s['title'].strip()
        # إذا العنوان طويل ويحتوي على "الحلقة" نستخدم extract_series_name
        if 'الحلقة' in s['title'] or 'Episode' in s['title']:
            cleaned = extract_series_name(s['title'])
            if cleaned:
                s['title'] = cleaned
    # جميع الحلقات
    episodes = []
    seen = set()
    for m in re.finditer(r'<a\s+href="(https?://[^"]*watch\.php\?vid=([a-f0-9]+))"[^>]*>(.*?)</a>', html, re.DOTALL):
        vid2 = m.group(2)
        if vid2 in seen: continue
        seen.add(vid2)
        ep_title = re.sub(r'<[^>]+>', '', m.group(3)).strip()
        # تخطي روابط التنقل (الحلقة السابقة/التالية)
        if 'السابقة' in ep_title or 'التالية' in ep_title or 'التالي' in ep_title or 'السابق' in ep_title:
            continue
        ep_num = extract_ep_num(ep_title)
        if ep_num == 0:
            continue
        episodes.append({'number': ep_num, 'vid': vid2, 'url': m.group(1), 'title': ep_title})
    if episodes:
        episodes.sort(key=lambda e: e['number'])
        s['episodes'] = episodes
    return s

def run_detail(series_list, workers, resume=False):
    total = len(series_list)
    path = os.path.join(DATA_DIR, 'results_detail.json')
    if resume and os.path.exists(path):
        existing_series = load_json(path)
        exist_names = {s.get('seriesName', ''): s for s in existing_series if s.get('seriesName')}
        p(f'📂 تحميل {len(existing_series)} مسلسل من النتائج السابقة')
    else:
        existing_series = []
        exist_names = {}
    done = 0
    def process(s):
        name = s['seriesName']
        if name in exist_names and exist_names[name].get('episodes'):
            p(f'  ✅ [{done+1}/{total}] {name[:40]} - {len(exist_names[name]["episodes"])} حلقات (مسبقاً)')
            return exist_names[name]
        time.sleep(0.5)
        for ep in s['episodes']:
            try:
                det = watch_detail(ep['vid'])
                if det.get('title'):
                    det['seriesName'] = name
                    if det.get('episodes'):
                        s['episodes'] = det['episodes']
                    else:
                        det['episodes'] = s['episodes']
                    s.update(det)
                    p(f'  ✅ [{done+1}/{total}] {name[:40]} - {len(s.get("episodes", []))} حلقات')
                    return s
            except Exception as e:
                continue
        p(f'  ⚠ [{done+1}/{total}] {name[:40]} - أساسي')
        return s
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process, s): s for s in series_list}
        for f in as_completed(futs):
            done += 1
            try: f.result()
            except: pass
            if done % 25 == 0:
                cur = [exist_names.get(s['seriesName'], s) for s in series_list[:done]]
                save_json(path, cur)
                p(f'  💾 حفظ: {done}/{total}')
    final = [exist_names.get(s['seriesName'], s) for s in series_list]
    save_json(path, final)
    return final

# ===== المرحلة 3: السيرفرات =====
def view_servers(vid):
    html = fetch_text(f'{BASE}/view.php?vid={vid}')
    servers = []
    blocks = re.findall(r'<li[^>]*\s+id="server_([^"]+)"[^>]*\s+data-embed="(.*?)">.*?<strong>(.*?)</strong>', html, re.DOTALL)
    for sid, embed, sname in blocks:
        embed = embed.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#039;', "'")
        ifr = re.search(r"src='([^']+)'", embed)
        if not ifr: ifr = re.search(r'src="([^"]+)"', embed)
        servers.append({'name': sname.strip(), 'url': ifr.group(1) if ifr else ''})
    return servers

def run_servers(series_list, workers, resume=False):
    total = len(series_list)
    for i, s in enumerate(series_list, 1):
        name = s.get('seriesName', '')
        eps = s.get('episodes', [])
        todo = [ep for ep in eps if not ep.get('servers')]
        if not todo:
            ts = sum(len(ep.get('servers', [])) for ep in eps)
            p(f'  ✅ [{i}/{total}] {name[:40]} ({len(eps)} حلقات, {ts} سيرفر) مسبقاً')
            continue
        def handle(ep):
            for att in range(3):
                try:
                    time.sleep(0.3)
                    sv = view_servers(ep['vid'])
                    if sv:
                        ep['servers'] = sv
                        return
                except:
                    if att < 2:
                        time.sleep(2)
                        continue
                    return
        with ThreadPoolExecutor(max_workers=min(workers, 6)) as ex:
            list(ex.map(handle, todo))
        ts = sum(len(ep.get('servers', [])) for ep in eps)
        p(f'  ✅ [{i}/{total}] {name[:40]} - {len(eps)} حلقات, {ts} سيرفر')
        if i % 10 == 0:
            save_json(os.path.join(DATA_DIR, 'results_royal_anime.json'), series_list)
    save_json(os.path.join(DATA_DIR, 'results_royal_anime.json'), series_list)
    return series_list

# ===== التحويل لصيغة الموقع =====
def to_site_format(series_list):
    """تحويل النتائج لصيغة data-anime-series.js"""
    out = []
    for s in series_list:
        eps = s.get('episodes', [])
        if not eps:
            continue
        seasons = []
        all_eps = []
        for ep in eps:
            servers = []
            for sv in ep.get('servers', []):
                entry = {'name': sv.get('name', ''), 'url': sv.get('url', '') or sv.get('embedUrl', '')}
                servers.append(entry)
            all_eps.append({
                'episodeNumber': ep.get('number', 0),
                'title': ep.get('title', ''),
                'duration': ep.get('duration', ''),
                'servers': servers,
            })
        all_eps.sort(key=lambda e: e['episodeNumber'])
        # استخراج الصورة من أول حلقة
        poster = s.get('poster', '')
        if not poster and eps:
            poster = eps[0].get('thumbnail', '')
        # استخدام seriesName الأصلي كعنوان (أنظف من title المستخرج من H1)
        series_title = s.get('seriesName', '')
        if not series_title:
            series_title = s.get('title', '')
        # تنظيف العنوان من "انمي" البادئة والفراغات الزائدة
        series_title = re.sub(r'^(?:انمي|movie|series|مسلسل|فيلم)\s+', '', series_title, flags=re.IGNORECASE).strip()
        item = {
            'title': series_title,
            'year': '',
            'rating': '',
            'type': 'انمي',
            'contentType': 'series',
            'description': s.get('description', ''),
            'cast': [],
            'poster': poster,
            'categories': s.get('categories', ['انمي']),
            'quality': '',
            'isComplete': False,
            'seasons': [{
                'seasonNumber': 1,
                'episodes': all_eps,
            }],
        }
        out.append(item)
    # ترتيب المسلسلات أبجدياً
    out.sort(key=lambda x: x['title'].strip())
    return out

def save_site_format(series_list, output_path=None):
    """حفظ النتائج بصيغة data-anime-series.js"""
    converted = to_site_format(series_list)
    if output_path is None:
        output_path = os.path.join(SCRIPT_DIR, 'data_anime_royal.js')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات أنمي من رويال دراما — {len(converted)} مسلسل\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('const cd_anime_series_royal = ')
        json.dump(converted, f, ensure_ascii=False, indent=2)
    p(f'📁 تم الحفظ: {output_path} ({len(converted)} مسلسل)')
    return output_path

# ===== دمج مع data-anime-series.js الحالي =====
def merge_with_existing(new_series, existing_path):
    """دمج المسلسلات الجديدة مع الملف الحالي مع تجنب التكرار"""
    if not os.path.exists(existing_path):
        p(f'⚠ الملف الحالي غير موجود: {existing_path}')
        return new_series
    with open(existing_path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'const cd_anime_series\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
    if not m:
        p('❌ لم يتم العثور على مصفوفة cd_anime_series في الملف')
        return new_series
    existing = json.loads(m.group(1))
    p(f'📂 تحميل {len(existing)} مسلسل من الملف الحالي')
    # تجنب التكرار باستخدام title موحد
    norm = lambda t: re.sub(r'\s+', '', (t or '').strip()).lower()
    exist_titles = {norm(x['title']): x for x in existing}
    added = 0
    skipped = 0
    for item in new_series:
        t = norm(item['title'])
        if t in exist_titles:
            skipped += 1
        else:
            existing.append(item)
            exist_titles[t] = item
            added += 1
    p(f'✅ جديد: {added} | مكرر: {skipped} | الإجمالي: {len(existing)}')
    return existing

# ===== MAIN =====
def main():
    parser = argparse.ArgumentParser(description='سكربت سحب مسلسلات الأنمي من رويال دراما')
    parser.add_argument('--start', type=int, default=1, help='صفحة البداية (افتراضي: 1)')
    parser.add_argument('--end', type=int, default=1, help='صفحة النهاية (افتراضي: 1)')
    parser.add_argument('--workers', type=int, default=4, help='عدد العمال (افتراضي: 4)')
    parser.add_argument('--phase', choices=['all', 'listing', 'detail', 'servers'], default='all', help='المرحلة')
    parser.add_argument('--resume', action='store_true', help='استئناف من النتائج السابقة')
    parser.add_argument('--convert', action='store_true', help='تحويل نتائج JSON إلى صيغة الموقع فقط')
    parser.add_argument('--merge', type=str, default='', help='دمج مع ملف data-anime-series.js الحالي')
    parser.add_argument('--output', type=str, default='', help='ملف الإخراج')
    args = parser.parse_args()

    p('=' * 55)
    p(f'🎌 سحب أنمي رويال دراما - صفحات {args.start}-{args.end}')
    p(f'   عمال: {args.workers} | مرحلة: {args.phase}')
    p('=' * 55)

    # --convert: تحويل فقط
    if args.convert:
        path = os.path.join(DATA_DIR, 'results_royal_anime.json')
        if not os.path.exists(path):
            p(f'❌ الملف غير موجود: {path}')
            return
        series = load_json(path)
        p(f'📂 تحميل {len(series)} مسلسل من {path}')
        converted = to_site_format(series)
        output = args.output if args.output else os.path.join(DATA_DIR, '..', 'data_anime_royal.js')
        if args.merge:
            # دمج مع الملف الحالي قبل الحفظ
            merged = merge_with_existing(converted, args.merge)
            with open(output, 'w', encoding='utf-8') as f:
                f.write(f'// مسلسلات أنمي — {len(merged)} مسلسل (بعد الدمج)\n')
                f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write('const cd_anime_series = ')
                json.dump(merged, f, ensure_ascii=False, indent=2)
            p(f'📁 تم حفظ الدمج: {output} ({len(merged)} مسلسل)')
        else:
            save_site_format(converted, output)
        return

    # التحميل من النتائج السابقة للسيرفرات
    if args.phase in ('servers', 'all'):
        serv_path = os.path.join(DATA_DIR, 'results_royal_anime.json')
        if args.resume and os.path.exists(serv_path):
            series = load_json(serv_path)
            p(f'📂 تحميل {len(series)} مسلسل من {serv_path}')
        else:
            series = None
    else:
        series = None

    # المرحلة 1: القائمة
    if series is None and args.phase in ('all', 'listing'):
        p('\n=== المرحلة 1: القائمة ===')
        items = run_listing(args.start, args.end, args.workers, resume=args.resume)
        p(f'📊 تجميع المسلسلات...')
        series = group_series(items)
        p(f'   {len(series)} مسلسل من {len(items)} حلقة')
        save_json(os.path.join(DATA_DIR, 'results_royal_anime.json'), series)
    elif series is None:
        for fname in ['results_royal_anime.json', 'results_detail.json', 'results_listing.json']:
            fp = os.path.join(DATA_DIR, fname)
            if os.path.exists(fp):
                series = load_json(fp)
                p(f'📂 تحميل {fname}: {len(series)} عنصر')
                break
        else:
            p('❌ لا توجد بيانات. شغّل --phase listing أولاً')
            return

    # المرحلة 2: التفاصيل
    if args.phase in ('all', 'detail'):
        p('\n=== المرحلة 2: تفاصيل المسلسلات ===')
        series = run_detail(series, args.workers, resume=args.resume)

    # المرحلة 3: السيرفرات
    if args.phase in ('all', 'servers'):
        p('\n=== المرحلة 3: السيرفرات ===')
        series = run_servers(series, args.workers, resume=args.resume)

    # حفظ النهائي
    final_path = os.path.join(DATA_DIR, 'results_royal_anime.json')
    save_json(final_path, series)
    total_eps = sum(len(s.get('episodes', [])) for s in series)
    total_srv = sum(sum(len(ep.get('servers', [])) for ep in s.get('episodes', [])) for s in series)
    p(f'\n✅ تم: {len(series)} مسلسل, {total_eps} حلقة, {total_srv} سيرفر')
    p(f'📁 {final_path}')

    # تحويل + دمج مع الملف الحالي
    converted = to_site_format(series)
    output = args.output if args.output else os.path.join(SCRIPT_DIR, 'data_anime_royal.js')
    if args.merge:
        merged = merge_with_existing(converted, args.merge)
        with open(output, 'w', encoding='utf-8') as f:
            f.write(f'// مسلسلات أنمي — {len(merged)} مسلسل (بعد الدمج)\n')
            f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write('const cd_anime_series = ')
            json.dump(merged, f, ensure_ascii=False, indent=2)
        p(f'📁 تم حفظ الدمج: {output}')
    else:
        save_site_format(converted, output)


if __name__ == '__main__':
    main()
