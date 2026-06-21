#!/usr/bin/env python3
"""
سكربت سحب مسلسلات من w9.royal-drama.com
الاستعمال:
  python scrape_royal.py --start 1 --end 50
  python scrape_royal.py --start 1 --end 10 --phase listing
  python scrape_royal.py --start 1 --end 50 --phase series
  python scrape_royal.py --phase servers
"""
import os, sys, re, json, time, argparse, copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = __import__('io').TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import requests

BASE = 'https://w9.royal-drama.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}
SES = requests.Session()
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

CATEGORIES = OrderedDict([
    ('asiawia',   'musalsalat-asiawia'),
    ('turkish',   'turkish-series-3sk'),
    ('arabic',    'arabic-series1-2024'),
    ('indian',    'indian-series-2025'),
    ('foreign',   'musalsalat-ajnabia-netflix'),
    ('anime',     'musalsalat-animiee-2025'),
    ('tvshows',   'tv-shows'),
    ('movies',    'aflams-2026-1'),
    ('ramadan',   'musalsalat-ramadan-2025'),
])

def p(text):
    try:
        print(text, flush=True)
    except:
        print(repr(text), flush=True)

def fetch(url, **kwargs):
    for att in range(5):
        try:
            r = SES.get(url, headers=HEADERS, timeout=30, **kwargs)
            r.raise_for_status()
            return r
        except Exception as e:
            if '429' in str(e) and att < 4:
                time.sleep(3 * (att + 1))
                continue
            if att < 4:
                time.sleep(2)
                continue
            raise

def fetch_text(url, **kwargs):
    return fetch(url, **kwargs).text

def save_json(path, data):
    tmp = path + '.tmp'
    c = copy.deepcopy(data)
    _clean(c)
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(c, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _clean(data):
    if isinstance(data, list):
        for it in data:
            _clean(it)
    elif isinstance(data, dict):
        for k in list(data.keys()):
            if k.startswith('_'):
                del data[k]
            else:
                _clean(data[k])

# ========== استخراج اسم المسلسل ==========
def extract_series_name(title):
    clean = re.sub(r'^(?:مسلسل|برنامج|فيلم|movie|series)\s+', '', title, flags=re.IGNORECASE).strip()
    m = re.match(r'(.*?)\s+الحلقة\s+\d+', clean)
    if m:
        n = m.group(1).strip()
        n = re.sub(r'\s+(?:مترجم|مدبلج|HD|FHD|SD|جميع الحلقات|جميع.*)$', '', n, flags=re.IGNORECASE).strip()
        return n
    m = re.match(r'(.*?)\s+حلقة\s+\d+', clean)
    if m:
        n = m.group(1).strip()
        n = re.sub(r'\s+(?:مترجم|HD|FHD|SD).*$', '', n, flags=re.IGNORECASE).strip()
        return n
    m = re.match(r'(.*?)\s+(?:Episode|Ep\.?)\s+\d+', clean, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    clean = re.sub(r'\s+(?:مترجم|مدبلج|HD|FHD|SD).*$', '', clean, flags=re.IGNORECASE).strip()
    return clean

def extract_ep_num(title):
    m = re.search(r'الحلقة\s+(\d+)', title)
    if m: return int(m.group(1))
    m = re.search(r'حلقة\s+(\d+)', title)
    if m: return int(m.group(1))
    m = re.search(r'(?:Episode|Ep\.?)\s+(\d+)', title, re.IGNORECASE)
    if m: return int(m.group(1))
    return 0

# ========== المرحلة 1: القائمة ==========
def listing_page(page, cat_slug='musalsalat-asiawia'):
    html = fetch_text(f'{BASE}/category3.php?cat={cat_slug}&page={page}&order=DESC')
    items = []
    cards = re.findall(r'<li class="col-xs-6 col-sm-4 col-md-3">(.*?)</li>', html, re.DOTALL)
    for card in cards:
        try:
            links = re.findall(r'<a\s+href="(https?://[^"]*watch\.php\?vid=([a-f0-9]+))"[^>]*>', card)
            if not links: continue
            ep_url, vid = links[0][0], links[0][1]
            tl = re.findall(r'<a\s+href="https?://[^"]*watch\.php\?vid=[a-f0-9]+"[^>]*\s+title="([^"]+)"', card)
            title = tl[0] if tl else ''
            dur = re.search(r'<span class="pm-label-duration">([^<]+)</span>', card)
            img = re.search(r'<img[^>]+src="([^"]+)"[^>]*>', card)
            esp = re.search(r'<span class="ep">الحلقة\s*(\d+)</span>', card)
            ep_n = int(esp.group(1)) if esp else extract_ep_num(title)
            items.append({
                'vid': vid, 'url': ep_url, 'title': title,
                'duration': dur.group(1).strip() if dur else '',
                'thumbnail': img.group(1) if img else '',
                'episodeNumber': ep_n, 'seriesName': extract_series_name(title),
            })
        except:
            continue
    return items

def scrape_listing(start, end, workers, cat_slug='musalsalat-asiawia'):
    path = os.path.join(DATA_DIR, f'results_listing_{cat_slug}.json')
    all_items = load_json(path) or []
    existing = {it['vid'] for it in all_items}
    pages = list(range(start, end + 1))
    with ThreadPoolExecutor(max_workers=min(workers, 8)) as ex:
        futs = {ex.submit(listing_page, p, cat_slug): p for p in pages}
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
                p(f'  ✅ صفحة {p_}: +{cnt} (المجموع {len(all_items)})')
            except Exception as e:
                p(f'  ❌ صفحة {p_}: {e}')
    save_json(path, all_items)
    p(f'📁 تم حفظ القائمة: {len(all_items)} حلقة')
    return all_items

# ========== تجميع المسلسلات ==========
def group_by_series(items):
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
    return list(sm.values())

# ========== المرحلة 2: التفاصيل ==========
def watch_detail(vid):
    html = fetch_text(f'{BASE}/watch.php?vid={vid}')
    s = {}
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html)
    if h1: s['title'] = h1.group(1).strip()
    img = re.search(r'<div class="pm-series-brief">.*?<img[^>]+src="([^"]+)"', html, re.DOTALL)
    if img: s['poster'] = img.group(1)
    desc = re.search(r'<div itemprop="description">\s*<p>(.*?)</p>', html, re.DOTALL)
    if not desc:
        desc = re.search(r'<div class="pm-series-description">.*?<p>(.*?)</p>', html, re.DOTALL)
    if desc: s['description'] = desc.group(1).strip()
    cats = re.findall(r'<dt>الاقسام</dt>\s*<dd>(.*?)</dd>', html, re.DOTALL)
    if cats:
        cl = re.findall(r'<a[^>]*>(.*?)</a>', cats[0])
        if cl: s['categories'] = [c.strip() for c in cl]
    tags = re.findall(r'<dt>الكلمات المفتاحية</dt>\s*<dd>(.*?)</dd>', html, re.DOTALL)
    if tags:
        tl = re.findall(r'<a[^>]*>(.*?)</a>', tags[0])
        if tl: s['tags'] = [t.strip() for t in tl]
    # استخراج الحلقات: نجد موضع SeasonsEpisodesMain ونأخذ كل watch.php بعده
    episodes = []
    seen = set()
    pos = html.find('SeasonsEpisodesMain')
    if pos >= 0:
        # نأخذ النص من SeasonsEpisodesMain لنهاية الصفحة أو لمكان القسم التالي
        section = html[pos:pos+50000]  # 50K حرف كافي للحلقات
        for m in re.finditer(r'<a\s+href="(https?://[^"]*watch\.php\?vid=([a-f0-9]+))"\s*(?:class="[^"]*"\s*)?title="([^"]*)"', section, re.DOTALL):
            v = m.group(2)
            if v in seen: continue
            seen.add(v)
            et = m.group(3).strip()
            et = re.sub(r'\s+', ' ', et).strip()
            if not et or 'السابقة' in et or 'التالية' in et:
                continue
            en = extract_ep_num(et)
            episodes.append({'number': en, 'vid': v, 'url': m.group(1), 'title': et})
        # إذا ما لقينا بالـ title، نجرب بدون title
        if not episodes:
            for m in re.finditer(r'<a\s+href="(https?://[^"]*watch\.php\?vid=([a-f0-9]+))"[^>]*>(.*?)</a>', section, re.DOTALL):
                v = m.group(2)
                if v in seen: continue
                seen.add(v)
                et = re.sub(r'<[^>]+>', '', m.group(3)).strip()
                et = re.sub(r'\s+', ' ', et).strip()
                if not et or 'السابقة' in et or 'التالية' in et:
                    continue
                en = extract_ep_num(et)
                episodes.append({'number': en, 'vid': v, 'url': m.group(1), 'title': et})
    if episodes:
        episodes.sort(key=lambda e: e['number'])
        s['episodes'] = episodes
        s['episodeCount'] = len(episodes)
    if episodes:
        sv = view_servers(episodes[0]['vid'])
        if sv:
            s['serverList'] = list(OrderedDict.fromkeys(x['name'] for x in sv))
    return s

def view_servers(vid):
    html = fetch_text(f'{BASE}/view.php?vid={vid}')
    servers = []
    blocks = re.findall(r'<li[^>]*\s+id="server_([^"]+)"[^>]*\s+data-embed="(.*?)">.*?<strong>(.*?)</strong>', html, re.DOTALL)
    for sid, embed, sname in blocks:
        embed = embed.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#039;', "'")
        ifr = re.search(r"src='([^']+)'", embed)
        if not ifr: ifr = re.search(r'src="([^"]+)"', embed)
        servers.append({'id': sid, 'name': sname.strip(), 'embedUrl': ifr.group(1) if ifr else ''})
    return servers

def scrape_detail(series_list, workers):
    total = len(series_list)
    path = os.path.join(DATA_DIR, 'results_detail.json')
    existing = load_json(path) or []
    exist_names = {s.get('seriesName', ''): s for s in existing if s.get('seriesName')} if existing else {}
    done = 0

    def process(s):
        name = s['seriesName']
        if name in exist_names and exist_names[name].get('episodes'):
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
                    return s
            except:
                continue
        return s

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process, s): s for s in series_list}
        for f in as_completed(futs):
            done += 1
            try:
                s = f.result()
                exist_names[s['seriesName']] = s
            except:
                pass
            if done % 25 == 0:
                save_json(path, list(exist_names.values()))
                p(f'  💾 نقطة حفظ: {done}/{total}')

    final = [exist_names.get(s['seriesName'], s) for s in series_list]
    save_json(path, final)
    return final

# ========== المرحلة 3: السيرفرات ==========
def scrape_servers(series_list, workers):
    total = len(series_list)
    for i, s in enumerate(series_list, 1):
        name = s.get('seriesName', '')
        eps = s.get('episodes', [])
        todo = [ep for ep in eps if not ep.get('servers')]
        if not todo:
            ts = sum(len(ep.get('servers', [])) for ep in eps)
            p(f'  ✅ [{i}/{total}] {name[:40]} - {len(eps)} حلقات, {ts} سيرفر (مسبقاً)')
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

        with ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(handle, todo))

        ts = sum(len(ep.get('servers', [])) for ep in eps)
        p(f'  ✅ [{i}/{total}] {name[:40]} - {len(eps)} حلقات, {ts} سيرفر')

        if i % 10 == 0:
            save_json(os.path.join(DATA_DIR, 'results_royal.json'), series_list)
            p(f'  💾 نقطة حفظ: {i}/{total}')

    save_json(os.path.join(DATA_DIR, 'results_royal.json'), series_list)
    return series_list

# ========== MAIN ==========
def main():
    parser = argparse.ArgumentParser(description='سحب مسلسلات رويال دراما')
    parser.add_argument('--start', type=int, default=1, help='صفحة البداية')
    parser.add_argument('--end', type=int, default=1, help='صفحة النهاية')
    parser.add_argument('--workers', type=int, default=4, help='عدد العمال')
    parser.add_argument('--phase', choices=['all', 'listing', 'series', 'servers'], default='all',
                        help='listing=قائمة, series=تفاصيل, servers=سيرفرات, all=الكل')
    parser.add_argument('--max', type=int, default=0, help='حد أقصى للمسلسلات')
    cat_keys = list(CATEGORIES.keys())
    parser.add_argument('--cat', default='asiawia', choices=['all'] + cat_keys,
                        help=f'القسم: all=الكل, {", ".join(cat_keys)}')
    args = parser.parse_args()

    cat_labels = {v: k for k, v in CATEGORIES.items()}

    if args.cat == 'all' and args.phase in ('all', 'listing'):
        # سحب جميع الأقسام
        all_items = []
        for cat_slug in CATEGORIES.values():
            cat_name = cat_labels[cat_slug]
            p(f'\n📂 القسم: {cat_name} ({cat_slug})')
            items = scrape_listing(args.start, args.end, args.workers, cat_slug)
            all_items.extend(items)
        # دمج كل القوائم
        merged, seen = [], set()
        for it in all_items:
            if it['vid'] not in seen:
                merged.append(it)
                seen.add(it['vid'])
        items = merged
        p(f'\n📊 الإجمالي: {len(items)} حلقة من جميع الأقسام')
    elif args.phase in ('all', 'listing'):
        item_cat = CATEGORIES[args.cat]
        items = scrape_listing(args.start, args.end, args.workers, item_cat)
    else:
        # تحميل البيانات من المراحل السابقة
        items = load_json(os.path.join(DATA_DIR, 'results_royal.json')) or []
        if not items:
            for cat_slug in CATEGORIES.values():
                lst = load_json(os.path.join(DATA_DIR, f'results_listing_{cat_slug}.json')) or []
                items.extend(lst)
        if not items:
            p('❌ لا توجد بيانات محفوظة. شغّل مرحلة listing أولاً.')
            return
        p(f'📂 تم تحميل {len(items)} عنصر')

    if args.phase in ('all', 'listing'):
        p(f'\n📊 تجميع المسلسلات...')
        series = group_by_series(items)
        p(f'   {len(series)} مسلسل من {len(items)} حلقة')
    elif args.phase == 'series':
        series = items if isinstance(items, list) and items and 'seriesName' in items[0] else group_by_series(items)
        p(f'📊 {len(series)} مسلسل')
    else:
        series = items if isinstance(items, list) else []

    if args.max > 0:
        series = series[:args.max]

    if args.phase in ('all', 'series'):
        p('\n--- المرحلة 2: تفاصيل المسلسلات ---')
        series = scrape_detail(series, args.workers)

    if args.phase == 'listing':
        save_json(os.path.join(DATA_DIR, 'results_royal.json'), series)
        total_eps = sum(len(s.get('episodes', [])) for s in series)
        p(f'\n✅ تم: {len(series)} مسلسل, {total_eps} حلقة')
        return

    if args.phase in ('all', 'servers'):
        p('\n--- المرحلة 3: سحب السيرفرات ---')
        series = scrape_servers(series, args.workers)
    elif args.phase == 'series':
        save_json(os.path.join(DATA_DIR, 'results_royal.json'), series)
        total_eps = sum(len(s.get('episodes', [])) for s in series)
        p(f'\n✅ تم: {len(series)} مسلسل, {total_eps} حلقة')
        return

    total_eps = sum(len(s.get('episodes', [])) for s in series)
    total_srv = sum(sum(len(ep.get('servers', [])) for ep in s.get('episodes', [])) for s in series)
    p(f'\n✅ تم: {len(series)} مسلسل, {total_eps} حلقة, {total_srv} سيرفر')
    p(f'📁 الملف: {os.path.join(DATA_DIR, "results_royal.json")}')

if __name__ == '__main__':
    main()
