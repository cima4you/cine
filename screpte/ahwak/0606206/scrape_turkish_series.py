#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت سحب مسلسلات تركية من yam.ahwaktv.net
مثل سكربت المسلسلات الأجنبية من tuktukhd

الاستعمال:
  python scrape_turkish_series.py --start 1 --end 3 --workers 4
  python scrape_turkish_series.py --phase listing
  python scrape_turkish_series.py --resume
  python scrape_turkish_series.py --convert --merge "data/data-turkish-completed.js" --output "data/data-turkish-completed.js"
"""
import os, sys, json, re, time, argparse, copy
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = __import__('io').TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import urllib.request, urllib.parse

BASE_URL = 'https://yam.ahwaktv.net'
CAT_URL = BASE_URL + '/category.php?cat=moslslat-turkiaa-motrgma'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DELAY = 0.3

def p(text, **kwargs):
    try: print(text, flush=True, **kwargs)
    except: print(repr(text), flush=True)

def fetch(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=30)
            return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise

def fetch_text(url, **kwargs):
    return fetch(url)

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

def clean_title(t):
    t = re.sub(r'^مسلسل\s+', '', t)
    t = re.sub(r'\s+مترجم\s*$', '', t)
    t = re.sub(r'\s+مدبلج\s*$', '', t)
    t = re.sub(r'\s+مدبلجة\s*$', '', t)
    t = re.sub(r'\s+مترجمة\s*$', '', t)
    t = re.sub(r'\s*-\s*$', '', t)
    return t.strip()

def arabic_only(t):
    return re.sub(r'[a-zA-Z\s]', '', t).strip()

def extract_series_name(title):
    """استخراج اسم المسلسل من عنوان حلقة (مثلاً 'أخي الحلقة 12 الثانية عشر' → 'أخي')"""
    t = clean_title(title)
    t = re.sub(r'\s*الحلقة\s*\d+.*$', '', t).strip()
    t = re.sub(r'\s+\d+\s*$', '', t).strip()
    return t

def extract_highest_ep(items):
    """إيجاد أعلى رقم حلقة في مجموعة من المداخل"""
    highest = 0
    best = items[0]
    for item in items:
        m = re.search(r'الحلقة\s*(\d+)', item.get('title', ''))
        ep = int(m.group(1)) if m else 0
        if ep > highest:
            highest = ep
            best = item
    return best, highest

def dedup_key(item, exist_data=None):
    """مفتاح موحد للديدب: first arabic_only, fallback extract_series_name, fallback url"""
    title = item.get('title', '')
    key = extract_series_name(title)
    akey = arabic_only(key)
    return akey or key or item.get('url', '')

def dedup_listing(items, exist_data=None):
    """إزالة تكرار المسلسلات من القائمة:
    - تجميع حسب الاسم الموحد
    - الاحتفاظ بالمدخل الذي له أعلى رقم حلقة (الأكثر اكتمالاً)
    - بين المداخل المتساوية، الأحتفاظ بالذي يحتوي أحرف لاتينية أكثر (لأنه يعطي اسم مسلسل أدق)"""
    groups = {}
    for item in items:
        key = dedup_key(item, exist_data) or item.get('url', '')
        groups.setdefault(key, []).append(item)
    out = []
    for key, group in groups.items():
        best, highest = extract_highest_ep(group)
        best['_max_ep'] = highest
        out.append(best)
    return out

# ===== المرحلة 1: القائمة =====
def listing_page(page):
    url = f'{CAT_URL}&page={page}' if page > 1 else CAT_URL
    html = fetch_text(url)
    items = []
    # مسلسلات
    cards = re.findall(
        r'<div class="col-xs-6[^"]*"[^>]*>.*?<a href="(https://yam\.ahwaktv\.net/[^"]+)".*?<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"',
        html, re.DOTALL
    )
    seen = set()
    for href, poster, alt in cards:
        if href in seen:
            continue
        seen.add(href)
        title = clean_title(alt) if alt else ''
        items.append({
            'url': href,
            'title': title,
            'poster': poster,
        })
    # أفلام
    movie_cards = re.findall(
        r'<a href="(https://yam\.ahwaktv\.net/watch\.php\?vid=[^"]+)".*?<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"',
        html, re.DOTALL
    )
    for href, poster, alt in movie_cards:
        if href in seen:
            continue
        seen.add(href)
        title = clean_title(alt) if alt else ''
        items.append({
            'url': href,
            'title': title,
            'poster': poster,
        })
    return items

def run_listing(start, end, workers, resume=False):
    path = os.path.join(DATA_DIR, 'turkish_series_listing.json')
    all_items = load_json(path) if resume else []
    existing = {it['url'] for it in all_items}
    pages = list(range(start, end + 1))
    with ThreadPoolExecutor(max_workers=min(workers, 8)) as ex:
        futs = {ex.submit(listing_page, p): p for p in pages}
        for f in as_completed(futs):
            p_ = futs[f]
            try:
                new = f.result()
                cnt = sum(1 for it in new if it['url'] not in existing and not existing.add(it['url']) and all_items.append(it) is None)
                p(f'  ✅ صفحة {p_}: +{cnt} ({len(all_items)})')
            except Exception as e:
                p(f'  ❌ صفحة {p_}: {e}')
    save_json(path, all_items)
    p(f'📁 القائمة: {len(all_items)} مسلسل')
    return all_items

# ===== المرحلة 2: التفاصيل =====
def extract_vid(url):
    m = re.search(r'[?&]vid=([0-9a-fA-F]+)', url)
    return m.group(1) if m else ''

def extract_ep_num(text):
    m = re.search(r'الحلقة\s*(\d+)', text)
    return int(m.group(1)) if m else 0

def _extract_ep_data(tag_html):
    """استخراج vid, title, ep_number من HTML وسم <a> للحلقة"""
    hm = re.search(r'href="(watch\.php\?vid=[0-9a-fA-F]+)"', tag_html)
    if not hm:
        hm = re.search(r"href='(watch\.php\?vid=[0-9a-fA-F]+)'", tag_html)
    if not hm:
        return None
    vid = hm.group(1)
    tm = re.search(r'title="([^"]*)"', tag_html)
    if not tm:
        tm = re.search(r"title='([^']*)'", tag_html)
    title = tm.group(1).strip() if tm else ''
    em = re.search(r'<em>(\d+)</em>', tag_html)
    ep_num = int(em.group(1)) if em else extract_ep_num(title)
    return {'vid': vid, 'title': title, 'episodeNumber': ep_num}

def parse_episodes_from_tabcontent(tab_html, season_number):
    """استخراج الحلقات من داخل tabcontent لموسم معين"""
    episodes, seen_urls = [], set()
    for m in re.finditer(r'<a[^>]+href="?(watch\.php\?vid=[0-9a-fA-F]+)"?[^>]*>.*?</a>', tab_html, re.DOTALL):
        data = _extract_ep_data(m.group(0))
        if not data or not data['episodeNumber']:
            continue
        url = BASE_URL + '/' + data['vid']
        if url in seen_urls:
            continue
        seen_urls.add(url)
        episodes.append({
            'url': url,
            'title': data['title'],
            'episodeNumber': data['episodeNumber'],
            'seasonNumber': season_number,
        })
    return episodes

def try_serie_page(serie_url, series_name_guess):
    """محاولة سحب الحلقات من صفحة المسلسل (view-serie.php)"""
    try:
        html = fetch_text(serie_url)
        if not html or 'هذا المسلسل غير متوفر' in html:
            return None, None
        episodes, seasons = [], []
        # Find season tabs
        tab_m = re.finditer(r"""<button[^>]*onclick="openCity\(event,\s*'Season(\d+)'\)"[^>]*>([^<]+)</button>""", html)
        for m in tab_m:
            sn = int(m.group(1))
            sname = m.group(2).strip()
            seasons.append({'seasonNumber': sn, 'name': sname})
            # Get tabcontent for this season (ends with </ul>\s*</div>)
            cont = re.search(
                r'<div[^>]*id="Season%d"[^>]*class="tabcontent"[^>]*>(.*?</ul>)\s*</div>' % sn,
                html, re.DOTALL
            )
            if cont:
                eps = parse_episodes_from_tabcontent(cont.group(1), sn)
                episodes.extend(eps)
        if episodes:
            episodes.sort(key=lambda e: (e['seasonNumber'], e['episodeNumber']))
            return episodes, seasons
    except:
        pass
    return None, None

def parse_season_section(html):
    """استخراج الحلقات من قسم SeasonsBox في صفحة المشاهدة (يبحث في كامل HTML)"""
    episodes, seasons = [], []
    tab_m = re.finditer(r"""<button[^>]*onclick="openCity\(event,\s*'Season(\d+)'\)"[^>]*>([^<]+)</button>""", html)
    for m in tab_m:
        sn = int(m.group(1))
        sname = m.group(2).strip()
        seasons.append({'seasonNumber': sn, 'name': sname})
        cont = re.search(
            r'<div[^>]*id="Season%d"[^>]*class="tabcontent"[^>]*>(.*?</ul>)\s*</div>' % sn,
            html, re.DOTALL
        )
        if cont:
            eps = parse_episodes_from_tabcontent(cont.group(1), sn)
            episodes.extend(eps)
    if episodes:
        episodes.sort(key=lambda e: (e['seasonNumber'], e['episodeNumber']))
    return episodes, seasons

def series_detail(item):
    url = item['url']
    html = fetch_text(url)
    det = {'url': url}
    vid = extract_vid(url)
    det['vid'] = vid
    det['poster'] = item.get('poster', '')

    # Extract real series name + serie page URL
    series_name = ''
    serie_url = ''
    m = re.search(r'view-serie\.php\?name=([^"\'&]+)', html)
    if m:
        name_param = m.group(1)
        series_name = urllib.parse.unquote(name_param.replace('-', ' ').replace('+', ' '))
        series_name = clean_title(series_name)
        serie_url = BASE_URL + '/view-serie.php?name=' + name_param
    
    if not series_name:
        name_m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if name_m:
            raw = name_m.group(1).strip()
            raw = clean_title(raw)
            raw = re.sub(r'\s*الحلقة\s*\d+.*$', '', raw).strip()
            series_name = raw

    det['title'] = series_name or item.get('title', '')
    
    # Description & poster
    desc_m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html, re.IGNORECASE)
    if desc_m:
        det['description'] = desc_m.group(1).strip()
    og_m = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
    if og_m:
        det['poster'] = og_m.group(1)

    # Try 1: series page (view-serie.php) — full season/episode structure
    episodes, seasons = None, None
    if serie_url:
        episodes, seasons = try_serie_page(serie_url, series_name)

    # Try 2: watch page seasons section (SeasonsBox)
    if not episodes:
        episodes, seasons = parse_season_section(html)

    # Try 3: legacy — all watch.php?vid= links (filtered by series name)
    if not episodes:
        ep_links = re.findall(
            r'<a\s+href="(https://yam\.ahwaktv\.net/watch\.php\?vid=[0-9a-fA-F]+)"[^>]*>([^<]*)</a>',
            html
        )
        episodes = []
        for eurl, etitle in ep_links:
            ep_num = extract_ep_num(etitle)
            if ep_num == 0:
                continue
            # Only include if title contains series name
            if series_name and series_name not in etitle and series_name not in etitle.replace('مسلسل ', ''):
                continue
            episodes.append({
                'episodeNumber': ep_num,
                'seasonNumber': 1,
                'title': etitle.strip(),
                'url': eurl,
            })
        if episodes:
            episodes.sort(key=lambda e: e['episodeNumber'])
            seasons = [{'seasonNumber': 1, 'name': 'الموسم 1'}]

    if episodes:
        det['episodes'] = episodes
        det['seasons'] = seasons or [{'seasonNumber': 1, 'name': 'الموسم 1'}]

    return det

def run_detail(series_list, workers, resume=False):
    path = os.path.join(DATA_DIR, 'turkish_series_detail.json')
    if resume and os.path.exists(path):
        existing = load_json(path)
        exist_urls = {s.get('url', ''): s for s in existing if s.get('url')}
        p(f'📂 تحميل {len(existing)} مسلسل من النتائج السابقة')
    else:
        existing = []
        exist_urls = {}
    todo = [s for s in series_list if s['url'] not in exist_urls]
    raw_results = existing[:]

    def process(s):
        time.sleep(DELAY)
        return series_detail(s)

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process, s): s for s in todo}
        for f in as_completed(futs):
            done += 1
            s = futs[f]
            try:
                det = f.result()
                raw_results.append(det)
                eps = len(det.get('episodes', []))
                p(f'  ✅ [{done}/{len(todo)}] {det.get("title", "")[:40]} - {eps} حلقات')
            except Exception as e:
                p(f'  ❌ [{done}/{len(todo)}] {s.get("title", "")[:40]}: {e}')
                raw_results.append(s)
            if done % 25 == 0:
                # Deduplicate before saving
                save_json(path, dedup_by_title(raw_results))
                p(f'  💾 حفظ: {done}/{len(todo)}')

    # Final dedup: keep one entry per series (the one with most episodes)
    results = dedup_by_title(raw_results)
    save_json(path, results)
    p(f'📁 التفاصيل: {len(results)} مسلسل (من {len(raw_results)} raw — إزالة {len(raw_results)-len(results)} تكرار)')
    return results

def dedup_by_title(items):
    """Keep one entry per normalized title (the one with most episodes)"""
    groups = {}
    for item in items:
        title = item.get('title', '').strip()
        key = re.sub(r'\s+', '', title).lower()
        key = re.sub(r'[\u064B-\u0652]', '', key)
        if not key:
            continue
        groups.setdefault(key, []).append(item)
    result = []
    for key, group in groups.items():
        best = max(group, key=lambda x: len(x.get('episodes', [])))
        result.append(best)
    return result

# ===== المرحلة 3: السيرفرات =====
def fetch_see_page(vid):
    url = f'{BASE_URL}/see.php?vid={vid}'
    return fetch(url)

def extract_servers(html):
    servers = []
    for m in re.finditer(r'<li[^>]*data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
        url = m.group(1)
        name = m.group(2).strip()
        if url and name:
            servers.append({'name': name, 'url': url, 'isDefault': len(servers) == 0})
    if not servers:
        for m in re.finditer(r'data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
            url = m.group(1)
            name = m.group(2).strip()
            if url and name:
                servers.append({'name': name, 'url': url, 'isDefault': len(servers) == 0})
    # Fallback: extract direct iframe from #Playerholder if no server list
    if not servers:
        m = re.search(r'<iframe[^>]*src="([^"]+)"', html)
        if m:
            servers.append({'name': 'Vidspeeds', 'url': m.group(1), 'isDefault': True})
    # Sort: Vidspeed first
    vidspeed = [s for s in servers if 'vidspeed' in s['name'].lower() or 'vidspeed' in s['url'].lower()]
    others = [s for s in servers if s not in vidspeed]
    servers = vidspeed + others
    for i, s in enumerate(servers):
        s['isDefault'] = (i == 0)
    return servers

def episode_servers(ep_url):
    vid = extract_vid(ep_url)
    if not vid:
        return [{'name': 'رابط المشاهدة', 'url': ep_url, 'isDefault': True}]
    html = fetch_see_page(vid)
    servers = extract_servers(html) if html else []
    return servers

def run_servers(series_list, workers, resume=False):
    path = os.path.join(DATA_DIR, 'turkish_series_full.json')
    if resume and os.path.exists(path):
        series_list = load_json(path)
        p(f'📂 تحميل {len(series_list)} مسلسل من النتائج السابقة')

    total = len(series_list)
    eps_total = sum(len(s.get('episodes', [])) for s in series_list)
    eps_done = 0

    for i, s in enumerate(series_list, 1):
        name = s.get('title', '')
        eps = s.get('episodes', [])
        todo = [ep for ep in eps if not ep.get('servers')]
        if not todo:
            ts = sum(len(ep.get('servers', {}).get('watch', [])) for ep in eps)
            eps_done += len(eps)
            p(f'  ✅ [{i}/{total}] {name[:40]} ({len(eps)} حلقات, {ts} سيرفر) موجود مسبقاً')
            continue

        def handle(ep):
            for att in range(2):
                try:
                    time.sleep(DELAY)
                    sv = episode_servers(ep['url'])
                    if sv:
                        ep['servers'] = sv
                        return True
                except:
                    if att < 1:
                        time.sleep(1)
                        continue
                    ep['servers'] = []
                    return False
            return False

        with ThreadPoolExecutor(max_workers=min(workers, 4)) as ex:
            fut_map = {ex.submit(handle, ep): ep for ep in todo}
            for f in as_completed(fut_map):
                ep = fut_map[f]
                eps_done += 1
                try:
                    f.result(timeout=25)
                except:
                    ep['servers'] = []
                p(f'    📡 [{eps_done}/{eps_total}] {name[:30]} - {ep.get("title","")[:30]}', end='\r')
            for f, ep in fut_map.items():
                if not f.done():
                    f.cancel()
                    ep['servers'] = []
                    eps_done += 1

        ts = sum(len(ep.get('servers', [])) for ep in eps)
        p(f'  ✅ [{i}/{total}] {name[:40]} - {len(eps)} حلقات, {ts} سيرفر    ')
        if i % 5 == 0:
            save_json(path, series_list)

    save_json(path, series_list)
    p(f'📁 السيرفرات: {len(series_list)} مسلسل, {eps_total} حلقة')
    return series_list

# ===== التحويل لصيغة الموقع =====
def to_site_format(series_list):
    out = []
    for s in series_list:
        title = s.get('title', '')
        if not title:
            continue
        seasons_out = []
        eps = s.get('episodes', [])
        season_info = s.get('seasons', [])
        eps_by_snum = {}
        for ep in eps:
            snum = ep.get('seasonNumber', 1)
            eps_by_snum.setdefault(snum, []).append(ep)
        seen_snums = set()
        for season in season_info:
            snum = season.get('seasonNumber', 0)
            if snum == 0:
                continue
            seen_snums.add(snum)
            ep_list = []
            for ep in eps_by_snum.pop(snum, []):
                sv = ep.get('servers', []) or []
                entry = {
                    'episodeNumber': ep.get('episodeNumber', 0),
                    'number': ep.get('episodeNumber', 0),
                    'title': ep.get('title', f'حلقة {ep.get("episodeNumber", "")}'),
                    'duration': '',
                    'servers': sv,
                    'downloadServers': [],
                }
                ep_list.append(entry)
            ep_list.sort(key=lambda e: e['episodeNumber'])
            seasons_out.append({'season': snum, 'seasonNumber': snum, 'episodes': ep_list})
        for snum in sorted(eps_by_snum):
            if snum in seen_snums:
                continue
            ep_list = []
            for ep in eps_by_snum[snum]:
                sv = ep.get('servers', []) or []
                entry = {
                    'episodeNumber': ep.get('episodeNumber', 0),
                    'number': ep.get('episodeNumber', 0),
                    'title': ep.get('title', f'حلقة {ep.get("episodeNumber", "")}'),
                    'duration': '',
                    'servers': sv,
                    'downloadServers': [],
                }
                ep_list.append(entry)
            ep_list.sort(key=lambda e: e['episodeNumber'])
            seasons_out.append({'season': snum, 'seasonNumber': snum, 'episodes': ep_list})
        seasons_out.sort(key=lambda x: x['season'])
        has_final = any('الاخيرة' in e.get('title','') or 'الأخيرة' in e.get('title','') for ep in eps for e in [ep])
        has_final_title = any(w in title for w in ['الاخيرة','والاخيرة','الأخيرة','والأخيرة','كاملة','كامله'])
        item = {
            'title': title,
            'year': '',
            'rating': '',
            'type': 'تركي',
            'contentType': 'series',
            'description': s.get('description', ''),
            'poster': s.get('poster', ''),
            'isComplete': has_final or has_final_title,
            'seasons': seasons_out,
        }
        out.append(item)
    out.sort(key=lambda x: x['title'].strip())
    return out

def save_site_format(data_list, output_path=None):
    if output_path is None:
        output_path = os.path.join(SCRIPT_DIR, 'data_turkish_series.js')
    var_name = 'cd_turkish_series'
    label = 'تركية'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات {label} من ahwak — {len(data_list)} مسلسل\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'const {var_name} = ')
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    p(f'📁 تم الحفظ: {output_path} ({len(data_list)} مسلسل)')
    return output_path

# ===== دمج مع ملف حالي =====
def merge_with_existing(existing, new_series):
    norm = lambda t: re.sub(r'\s+', '', (t or '').strip()).lower()
    exist_titles = {norm(x.get('title', '')): x for x in existing}
    added = 0
    updated = 0
    for item in new_series:
        t = norm(item.get('title', ''))
        if t in exist_titles:
            old = exist_titles[t]
            changed = False
            for key in ('rating', 'quality', 'description', 'poster'):
                if key in item and item[key] != old.get(key):
                    old[key] = item[key]
                    changed = True
            if 'seasons' in item and item['seasons']:
                old_seasons = {}
                for s in old.get('seasons', []):
                    sk = s.get('seasonNumber', s.get('season', 0))
                    old_seasons[sk] = s
                for s in item['seasons']:
                    sn = s.get('seasonNumber', 0) or s.get('season', 0)
                    if sn in old_seasons:
                        old_eps = {e.get('title', ''): e for e in old_seasons[sn].get('episodes', [])}
                        for e in s.get('episodes', []):
                            et = e.get('title', '')
                            if et in old_eps:
                                oe = old_eps[et]
                                if e.get('servers') and e['servers'] != oe.get('servers'):
                                    oe['servers'] = e['servers']
                                    changed = True
                            else:
                                old_seasons[sn].setdefault('episodes', []).append(e)
                                changed = True
                    else:
                        old.setdefault('seasons', []).append(s)
                        changed = True
            if changed:
                updated += 1
        else:
            existing.append(item)
            exist_titles[t] = item
            added += 1
    p(f'✅ جديد: {added} | محدث: {updated} | الإجمالي: {len(existing)}')
    return existing, added, updated

# ===== MAIN =====
def main():
    parser = argparse.ArgumentParser(description='سكربت سحب مسلسلات تركية من ahwak')
    parser.add_argument('--start', type=int, default=1, help='صفحة البداية (افتراضي: 1)')
    parser.add_argument('--end', type=int, default=1, help='صفحة النهاية (افتراضي: 1)')
    parser.add_argument('--workers', type=int, default=4, help='عدد العمال (افتراضي: 4)')
    parser.add_argument('--phase', choices=['all', 'listing', 'detail', 'servers'], default='all', help='المرحلة')
    parser.add_argument('--resume', action='store_true', help='استئناف من النتائج السابقة')
    parser.add_argument('--convert', action='store_true', help='تحويل نتائج JSON إلى صيغة الموقع فقط')
    parser.add_argument('--merge', nargs='?', type=str, const='auto', default='', help='دمج مع ملف حالي')
    parser.add_argument('--output', type=str, default='', help='ملف الإخراج')
    args = parser.parse_args()

    p('=' * 55)
    p(f'📺 سحب مسلسلات تركية من ahwak - صفحات {args.start}-{args.end}')
    p(f'   عمال: {args.workers} | مرحلة: {args.phase}')
    p('=' * 55)

    full_data_path = os.path.join(DATA_DIR, 'turkish_series_full.json')

    if args.convert:
        if os.path.exists(full_data_path):
            series_list = load_json(full_data_path)
        else:
            detail_path = os.path.join(DATA_DIR, 'turkish_series_detail.json')
            series_list = load_json(detail_path)
        if not series_list:
            p('❌ لا توجد بيانات للتحويل')
            return
        converted = to_site_format(series_list)

        completed = [x for x in converted if x.get('isComplete')]
        ongoing = [x for x in converted if not x.get('isComplete')]

        if args.merge:
            base_data = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))), 'data')
            mp_compl = args.merge if args.merge != 'auto' and 'completed' in args.merge else os.path.join(base_data, 'data-turkish-completed.js')
            mp_ongo = os.path.join(base_data, 'data-turkish-ongoing.js')
            # Use the --output flag to determine which file: default both
            for file_path, new_items, label, var_base in [
                (mp_compl, completed, 'المكتملة', 'cd_turkish_completed'),
                (mp_ongo, ongoing, 'المستمرة', 'cd_turkish_ongoing'),
            ]:
                if not os.path.exists(file_path):
                    p(f'📂 {label}: ملف جديد — إنشاء {len(new_items)} عنصر')
                    merged = new_items
                    var_name = var_base
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
                    if m:
                        existing = json.loads(m.group(2))
                        var_name = m.group(1)
                    else:
                        existing = []
                        var_name = var_base
                    p(f'📂 {label}: تحميل {len(existing)} عنصر من {file_path}')
                    merged, added, updated = merge_with_existing(existing, new_items)
                    p(f'✅ {label}: جديد {added} | محدث {updated} | الإجمالي {len(merged)}')

                with open(file_path, 'w', encoding='utf-8') as f:
                    lbl = 'منتهية' if 'completed' in file_path else 'مستمرة'
                    f.write(f'// مسلسلات تركية {lbl} — {len(merged)} مسلسل\n')
                    f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
                    f.write(f'const {var_name} = ')
                    json.dump(merged, f, ensure_ascii=False)
                p(f'📁 حفظ: {file_path} ({len(merged)} عنصر)')
        else:
            output_path = args.output or os.path.join(SCRIPT_DIR, 'data_turkish_series.js')
            save_site_format(converted, output_path)
        return

    # Phase 1: Listing
    series_list = []
    if args.phase in ('all', 'listing'):
        p(f'\n{"="*40}')
        p(f'المرحلة 1: سحب القائمة')
        p(f'{"="*40}')
        series_list = run_listing(args.start, args.end, args.workers, args.resume)
        if args.phase == 'listing':
            return
    else:
        detail_path = os.path.join(DATA_DIR, 'turkish_series_detail.json')
        if args.resume and os.path.exists(detail_path):
            series_list = load_json(detail_path)
            p(f'📂 تحميل {len(series_list)} مسلسل من التفاصيل السابقة')
        else:
            listing_path = os.path.join(DATA_DIR, 'turkish_series_listing.json')
            series_list = load_json(listing_path)
            p(f'📂 تحميل {len(series_list)} مسلسل من القائمة')

    if not series_list:
        p('❌ لا توجد مسلسلات للمعالجة')
        return

    # Dedup listing: keep one item per series before scraping details
    if args.phase in ('all', 'detail'):
        listing_before = len(series_list)
        series_list = dedup_listing(series_list)
        removed = listing_before - len(series_list)
        if removed:
            p(f'🔄 إزالة {removed} تكرار من القائمة — الاحتفاظ بـ {len(series_list)} مسلسل')
    
    # Phase 2: Detail
    if args.phase in ('all', 'detail'):
        p(f'\n{"="*40}')
        p(f'المرحلة 2: سحب التفاصيل')
        p(f'{"="*40}')
        series_list = run_detail(series_list, args.workers, args.resume)
        if args.phase == 'detail':
            return

    # Phase 3: Servers
    if args.phase in ('all', 'servers'):
        p(f'\n{"="*40}')
        p(f'المرحلة 3: سحب السيرفرات')
        p(f'{"="*40}')
        series_list = run_servers(series_list, args.workers, args.resume)

    # Save final + convert
    save_json(full_data_path, series_list)
    p(f'\n📁 البيانات النهائية: {full_data_path} ({len(series_list)} مسلسل)')

    converted = to_site_format(series_list)
    output_path = args.output or os.path.join(SCRIPT_DIR, 'data_turkish_series.js')
    save_site_format(converted, output_path)

    # Auto-merge to completed/ongoing files
    if args.merge:
        completed = [x for x in converted if x.get('isComplete')]
        ongoing = [x for x in converted if not x.get('isComplete')]
        base_data = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))), 'data')
        for file_path, new_items, label, var_base in [
            (os.path.join(base_data, 'data-turkish-completed.js'), completed, 'المكتملة', 'cd_turkish_completed'),
            (os.path.join(base_data, 'data-turkish-ongoing.js'), ongoing, 'المستمرة', 'cd_turkish_ongoing'),
        ]:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                m = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
                existing = json.loads(m.group(2)) if m else []
                var_name = m.group(1) if m else var_base
            else:
                existing = []
                var_name = var_base
            merged, added, updated = merge_with_existing(existing, new_items)
            with open(file_path, 'w', encoding='utf-8') as f:
                lbl = 'منتهية' if 'completed' in file_path else 'مستمرة'
                f.write(f'// مسلسلات تركية {lbl} — {len(merged)} مسلسل\n')
                f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'const {var_name} = ')
                json.dump(merged, f, ensure_ascii=False)
            p(f'📁 حفظ: {file_path} ({len(merged)} عنصر)')

if __name__ == '__main__':
    main()
