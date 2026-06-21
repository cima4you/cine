#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت سحب مسلسلات أجنبية من tuktukhd.com
الاستعمال:
  python scripts/tuktukhd/scrape_foreign_series.py --start 1 --end 3 --workers 4
  python scripts/tuktukhd/scrape_foreign_series.py --start 1 --end 3 --phase listing
  python scripts/tuktukhd/scrape_foreign_series.py --resume
  python scripts/tuktukhd/scrape_foreign_series.py --convert
  python scripts/tuktukhd/scrape_foreign_series.py --convert --merge split/data-foreign.js
"""
import os, sys, re, json, time, argparse, base64, copy
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = __import__('io').TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import requests

CAT_URL = 'https://tuktukhd.com/sercat/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%A7%D8%AC%D9%86%D8%A8%D9%8A/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}
SES = requests.Session()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def p(text, **kwargs):
    try: print(text, flush=True, **kwargs)
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
def extract_series_title(alt_text):
    """استخراج اسم المسلسل من alt/title النص"""
    if not alt_text:
        return ''
    # alt: "مسلسل From مترجم"
    clean = alt_text.strip()
    clean = re.sub(r'^(?:مسلسل|فيلم|انمي)\s+', '', clean).strip()
    clean = re.sub(r'\s+مترجم\s*$', '', clean).strip()
    return clean.strip()

def listing_page(page):
    url = f'{CAT_URL}?page={page}' if page > 1 else CAT_URL
    html = fetch_text(url)
    items = []
    cards = re.findall(r'<div class="Block--Item">(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
    if not cards:
        cards = re.findall(r'<div class="Block--Item">(.*?)</a>\s*</div>', html, re.DOTALL)
    for card in cards:
        try:
            href_m = re.search(r'href="(https://tuktukhd\.com/series/[^"]+)"', card)
            if not href_m:
                continue
            url = href_m.group(1)
            title = ''
            alt_m = re.search(r'alt="([^"]+)"', card)
            if alt_m:
                title = extract_series_title(alt_m.group(1))
            if not title:
                h2_m = re.search(r'<h2>(.*?)</h2>', card)
                if h2_m:
                    title = extract_series_title(h2_m.group(1))
            poster = ''
            poster_m = re.search(r'data-src="([^"]+)"', card)
            if poster_m:
                poster = poster_m.group(1)
            if not poster:
                poster_m = re.search(r'src="([^"]+)"', card)
                if poster_m:
                    poster = poster_m.group(1)
            genres = re.findall(r'<li>(.*?)</li>', card)
            items.append({
                'url': url,
                'title': title,
                'poster': poster,
                'genres': [g.strip() for g in genres if g.strip()],
            })
        except:
            continue
    return items

def run_listing(start, end, workers, resume=False):
    path = os.path.join(DATA_DIR, 'foreign_series_listing.json')
    all_items = load_json(path) if resume else []
    existing = {it['url'] for it in all_items}
    pages = list(range(start, end + 1))
    with ThreadPoolExecutor(max_workers=min(workers, 8)) as ex:
        futs = {ex.submit(listing_page, p): p for p in pages}
        for f in as_completed(futs):
            p_ = futs[f]
            try:
                new = f.result()
                cnt = 0
                for it in new:
                    if it['url'] not in existing:
                        all_items.append(it)
                        existing.add(it['url'])
                        cnt += 1
                p(f'  \u2705 \u0635\u0641\u062d\u0629 {p_}: +{cnt} ({len(all_items)})')
            except Exception as e:
                p(f'  \u274c \u0635\u0641\u062d\u0629 {p_}: {e}')
    save_json(path, all_items)
    p(f'\U0001f4c1 \u0627\u0644\u0642\u0627\u0626\u0645\u0629: {len(all_items)} \u0645\u0633\u0644\u0633\u0644')
    return all_items


# ===== المرحلة 2: التفاصيل =====
def series_detail(url):
    html = fetch_text(url)
    det = {}
    det['url'] = url
    h1 = re.search(r'<h1[^>]*class="[^"]*post-title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if h1:
        det['title'] = re.sub(r'<[^>]+>', '', h1.group(1)).strip()
    det['title'] = extract_series_title(det.get('title', ''))
    poster = re.search(r'<div class="image">\s*<img[^>]+src="([^"]+)"', html, re.DOTALL)
    if poster:
        det['poster'] = poster.group(1)
    if not det.get('poster'):
        pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if pm:
            det['poster'] = pm.group(1)
    desc = re.search(r'<div class="story">\s*<p>(.*?)</p>', html, re.DOTALL)
    if desc:
        det['description'] = re.sub(r'<[^>]+>', '', desc.group(1)).strip()
    if not det.get('description'):
        dm = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
        if dm:
            det['description'] = dm.group(1)
    rating = re.search(r'<div class="imdbS">.*?<strong>(.*?)</strong>', html, re.DOTALL)
    if rating:
        det['rating'] = rating.group(1).strip()
    details = {}
    for lt in ['\u0645\u0648\u0639\u062f \u0627\u0644\u0635\u062f\u0648\u0631 :', '\u062c\u0648\u062f\u0629 \u0627\u0644\u0645\u0633\u0644\u0633\u0644 :',
               '\u0644\u063a\u0629 \u0627\u0644\u0645\u0633\u0644\u0633\u0644 :', '\u062f\u0648\u0644\u0629 \u0627\u0644\u0645\u0633\u0644\u0633\u0644 :',
               '\u0627\u0644\u0639\u0645\u0631 :']:
        det_m = re.search(r'<span>' + re.escape(lt) + r'\s*</span>\s*<a[^>]*>([^<]+)</a>', html)
        if det_m:
            details[lt] = det_m.group(1).strip()
    year = ''
    if '\u0645\u0648\u0639\u062f \u0627\u0644\u0635\u062f\u0648\u0631 :' in details:
        year_text = details['\u0645\u0648\u0639\u062f \u0627\u0644\u0635\u062f\u0648\u0631 :']
        ym = re.search(r'(\d{4})', year_text)
        if ym:
            year = ym.group(1)
    if year:
        det['year'] = year
    quality = details.get('\u062c\u0648\u062f\u0629 \u0627\u0644\u0645\u0633\u0644\u0633\u0644 :', '')
    if quality:
        det['quality'] = quality
    if '\u0644\u063a\u0629 \u0627\u0644\u0645\u0633\u0644\u0633\u0644 :' in details:
        det['language'] = details['\u0644\u063a\u0629 \u0627\u0644\u0645\u0633\u0644\u0633\u0644 :']
    country = details.get('\u062f\u0648\u0644\u0629 \u0627\u0644\u0645\u0633\u0644\u0633\u0644 :', '')
    if country:
        det['country'] = country
    age = details.get('\u0627\u0644\u0639\u0645\u0631 :', '')
    if age:
        det['ageRating'] = age
    cast_m = re.search(r'<span>\u0628\u0637\u0648\u0644\u0629\s*:\s*</span>(.*?)</li>', html, re.DOTALL)
    if cast_m:
        cast_links = re.findall(r'<a[^>]*>([^<]+)</a>', cast_m.group(1))
        if cast_links:
            det['cast'] = [c.strip() for c in cast_links if c.strip() != '\u0639\u0631\u0636 \u0627\u0644\u0643\u0644']
    genres = []
    cs = re.search(r'<div class="catssection"[^>]*>(.*?)</section>', html, re.DOTALL)
    if cs:
        genre_li = re.search(r'<span>\u0627\u0644\u0627\u0646\u0648\u0627\u0639</span>(.*?)</li>', cs.group(1), re.DOTALL)
        if genre_li:
            genre_links = re.findall(r'<a[^>]*>([^<]+)</a>', genre_li.group(1))
            genres = [g.strip() for g in genre_links if g.strip()]
    if genres:
        det['genres'] = genres
    seasons = []
    ss = re.search(r'<section class="allseasonss"[^>]*>(.*?)</section>', html, re.DOTALL)
    if ss:
        season_blocks = re.findall(r'<a\s+href="(https://tuktukhd\.com/series/[^"]+)"[^>]*>.*?<h3>(.*?)</h3>', ss.group(1), re.DOTALL)
        for surl, sname in season_blocks:
            sn = re.sub(r'<[^>]+>', '', sname).strip()
            sn_m = re.search(r'\u0627\u0644\u0645\u0648\u0633\u0645\s*(\d+)', sn)
            season_num = int(sn_m.group(1)) if sn_m else 0
            if season_num > 0:
                seasons.append({'seasonNumber': season_num, 'name': sn, 'url': surl})
    if seasons:
        seasons.sort(key=lambda x: x['seasonNumber'])
        det['seasons'] = seasons
    episodes = []
    es = re.search(r'<section class="[^"]*allepcont[^"]*"[^>]*>(.*?)</section>', html, re.DOTALL)
    if es:
        ep_blocks = re.findall(r'<a\s+href="(https://tuktukhd\.com/[^"]*)"[^>]*title="([^"]*)"', es.group(1))
        for eurl, etitle in ep_blocks:
            ep_m = re.search(r'\u0627\u0644\u062d\u0644\u0642\u0629\s*(\d+)', etitle)
            ep_num = int(ep_m.group(1)) if ep_m else 0
            if ep_num == 0:
                continue
            episodes.append({
                'episodeNumber': ep_num,
                'title': f'\u062d\u0644\u0642\u0629 {ep_num}',
                'url': eurl,
                'thumbnail': '',
            })
    if episodes:
        episodes.sort(key=lambda e: e['episodeNumber'])
        # Tag with latest season number (episodes from the active tab)
        latest_snum = max([sn.get('seasonNumber', 0) for sn in seasons], default=1)
        for ep in episodes:
            ep['seasonNumber'] = latest_snum
        det['episodes'] = episodes
    return det

def run_detail(series_list, workers, resume=False):
    total = len(series_list)
    path = os.path.join(DATA_DIR, 'foreign_series_detail.json')
    if resume and os.path.exists(path):
        existing = load_json(path)
        exist_urls = {s.get('url', ''): s for s in existing if s.get('url')}
        p(f'\U0001f4c2 \u062a\u062d\u0645\u064a\u0644 {len(existing)} \u0645\u0633\u0644\u0633\u0644 \u0645\u0646 \u0627\u0644\u0646\u062a\u0627\u0626\u062c \u0627\u0644\u0633\u0627\u0628\u0642\u0629')
    else:
        existing = []
        exist_urls = {}
    todo = [s for s in series_list if s['url'] not in exist_urls]
    done = 0
    results = existing[:]
    def process(s):
        time.sleep(0.3)
        det = series_detail(s['url'])
        det.setdefault('title', s.get('title', ''))
        if not det.get('poster') and s.get('poster'):
            det['poster'] = s['poster']
        return det
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process, s): s for s in todo}
        for f in as_completed(futs):
            done += 1
            s = futs[f]
            try:
                det = f.result()
                results.append(det)
                eps = len(det.get('episodes', []))
                p(f'  \u2705 [{done}/{len(todo)}] {det.get("title", "")[:40]} - {eps} \u062d\u0644\u0642\u0627\u062a')
            except Exception as e:
                p(f'  \u274c [{done}/{len(todo)}] {s.get("title", "")[:40]}: {e}')
                results.append(s)
            if done % 25 == 0:
                save_json(path, results)
                p(f'  \U0001f4be \u062d\u0641\u0638: {done}/{len(todo)}')
    save_json(path, results)
    p(f'\U0001f4c1 \u0627\u0644\u062a\u0641\u0627\u0635\u064a\u0644: {len(results)} \u0645\u0633\u0644\u0633\u0644')
    return results


# ===== \u0627\u0644\u0645\u0631\u062d\u0644\u0629 3: \u062d\u0644\u0642\u0627\u062a \u0627\u0644\u0645\u0648\u0627\u0633\u0645 =====
def season_episodes(season_url, season_number):
    html = fetch_text(season_url)
    episodes = []
    es = re.search(r'<section class="[^"]*allepcont[^"]*"[^>]*>(.*?)</section>', html, re.DOTALL)
    if es:
        ep_blocks = re.findall(r'<a\s+href="(https://tuktukhd\.com/[^"]*)"[^>]*title="([^"]*)"', es.group(1))
        for eurl, etitle in ep_blocks:
            ep_m = re.search(r'\u0627\u0644\u062d\u0644\u0642\u0629\s*(\d+)', etitle)
            ep_num = int(ep_m.group(1)) if ep_m else 0
            if ep_num:
                episodes.append({
                    'episodeNumber': ep_num,
                    'seasonNumber': season_number,
                    'title': f'\u062d\u0644\u0642\u0629 {ep_num}',
                    'url': eurl,
                    'thumbnail': '',
                })
    episodes.sort(key=lambda e: e['episodeNumber'])
    return episodes

def run_seasons(series_list, workers, resume=False):
    total = len(series_list)
    path = os.path.join(DATA_DIR, 'foreign_series_full.json')
    existing_urls = set()
    for s in series_list:
        for ep in s.get('episodes', []):
            existing_urls.add(ep['url'])
    done = 0
    added_total = 0
    def process(s):
        season_info = s.get('seasons', [])
        local_added = 0
        for sn in season_info:
            snum = sn.get('seasonNumber', 0)
            if snum == 0:
                continue
            surl = sn.get('url', '')
            if not surl:
                continue
            existing = [ep for ep in s.get('episodes', []) if ep.get('seasonNumber') == snum]
            if existing:
                continue
            time.sleep(0.3)
            try:
                eps = season_episodes(surl, snum)
                if eps:
                    if 'episodes' not in s:
                        s['episodes'] = []
                    new_cnt = 0
                    for ep in eps:
                        if ep['url'] not in existing_urls:
                            s['episodes'].append(ep)
                            existing_urls.add(ep['url'])
                            new_cnt += 1
                    local_added += new_cnt
            except:
                pass
        return local_added
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process, s): s for s in series_list}
        for f in as_completed(futs):
            done += 1
            s = futs[f]
            try:
                added = f.result()
                added_total += added
                if added:
                    p(f'  \u2705 [{done}/{total}] {s.get("title", "")[:40]} +{added} \u062d\u0644\u0642\u0629')
            except Exception as e:
                p(f'  \u274c [{done}/{total}] {s.get("title", "")[:40]}: {e}')
            if done % 10 == 0:
                save_json(path, series_list)
    save_json(path, series_list)
    p(f'\U0001f4c1 \u0627\u0644\u0645\u0648\u0627\u0633\u0645: {len(series_list)} \u0645\u0633\u0644\u0633\u0644, +{added_total} \u062d\u0644\u0642\u0629 \u062c\u062f\u064a\u062f\u0629')
    return series_list


# ===== \u0627\u0644\u0645\u0631\u062d\u0644\u0629 4: \u0627\u0644\u0633\u064a\u0631\u0641\u0631\u0627\u062a =====
def episode_servers(ep_url):
    html = fetch_text(ep_url)
    servers = []
    crypts = re.findall(r'data-crypt="([^"]+)"', html)
    for c in crypts:
        try:
            watch_url = base64.b64decode(c).decode('utf-8')
            servers.append({'url': watch_url, 'isDefault': len(servers) == 0})
        except:
            pass
    si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', html, re.DOTALL)
    for i, s in enumerate(servers):
        if i < len(si):
            servers[i]['name'] = si[i].strip()
        else:
            servers[i]['name'] = f'TukTuk {i+1}'
    dl_links = re.findall(r'data-real-url="([^"]+)"', html)
    download = []
    for dl in dl_links:
        download.append({'name': 'TukTuk Download', 'url': dl})
    return {'watch': servers, 'download': download}

def run_servers(series_list, workers, resume=False):
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
            p(f'  \u2705 [{i}/{total}] {name[:40]} ({len(eps)} \u062d\u0644\u0642\u0627\u062a, {ts} \u0633\u064a\u0631\u0641\u0631) \u0645\u0633\u0628\u0642\u0627\u064b')
            continue

        def handle(ep):
            for att in range(2):
                try:
                    time.sleep(0.2)
                    sv = episode_servers(ep['url'])
                    if sv.get('watch'):
                        ep['servers'] = sv
                        return True
                except:
                    if att < 1:
                        time.sleep(1)
                        continue
                    ep['servers'] = {'watch': [], 'download': []}
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
                    ep['servers'] = {'watch': [], 'download': []}
                p(f'    \U0001f4e1 [{eps_done}/{eps_total}] {name[:30]} - {ep.get("title","")[:30]}', end='\r')
            # mark any remaining (unsubmitted/cancelled) as empty
            for f, ep in fut_map.items():
                if not f.done():
                    f.cancel()
                    ep['servers'] = {'watch': [], 'download': []}
                    eps_done += 1

        ts = sum(len(ep.get('servers', {}).get('watch', [])) for ep in eps)
        p(f'  \u2705 [{i}/{total}] {name[:40]} - {len(eps)} \u062d\u0644\u0642\u0627\u062a, {ts} \u0633\u064a\u0631\u0641\u0631    ')
        if i % 5 == 0:
            save_json(os.path.join(DATA_DIR, 'foreign_series_full.json'), series_list)
    save_json(os.path.join(DATA_DIR, 'foreign_series_full.json'), series_list)
    return series_list


# ===== \u0627\u0644\u062a\u062d\u0648\u064a\u0644 \u0644\u0635\u064a\u063a\u0629 \u0627\u0644\u0645\u0648\u0642\u0639 =====
def to_site_format(series_list):
    out = []
    for s in series_list:
        title = s.get('title', '')
        if not title:
            continue
        seasons_out = []
        eps = s.get('episodes', [])
        season_info = s.get('seasons', [])
        # Group episodes by seasonNumber
        eps_by_snum = {}
        for ep in eps:
            snum = ep.get('seasonNumber', 1)
            eps_by_snum.setdefault(snum, []).append(ep)
        # Build season entries from season_info order, populate with episodes
        seen_snums = set()
        for season in season_info:
            snum = season.get('seasonNumber', 0)
            if snum == 0:
                continue
            seen_snums.add(snum)
            ep_list = []
            for ep in eps_by_snum.pop(snum, []):
                sv = ep.get('servers', {})
                watch = sv.get('watch', []) if sv else []
                download = sv.get('download', []) if sv else []
                entry = {
                    'episodeNumber': ep.get('episodeNumber', 0),
                    'title': ep.get('title', f'\u062d\u0644\u0642\u0629 {ep.get("episodeNumber", "")}'),
                    'duration': '',
                    'servers': [{'name': w.get('name', ''), 'url': w.get('url', ''), 'isDefault': w.get('isDefault', False)} for w in watch],
                    'downloadServers': [{'name': d.get('name', ''), 'url': d.get('url', '')} for d in download],
                }
                ep_list.append(entry)
            ep_list.sort(key=lambda e: e['episodeNumber'])
            seasons_out.append({'seasonNumber': snum, 'episodes': ep_list})
        # Remaining episodes (from seasons not in season_info)
        for snum in sorted(eps_by_snum):
            if snum in seen_snums:
                continue
            ep_list = []
            for ep in eps_by_snum[snum]:
                sv = ep.get('servers', {})
                watch = sv.get('watch', []) if sv else []
                download = sv.get('download', []) if sv else []
                entry = {
                    'episodeNumber': ep.get('episodeNumber', 0),
                    'title': ep.get('title', f'\u062d\u0644\u0642\u0629 {ep.get("episodeNumber", "")}'),
                    'duration': '',
                    'servers': [{'name': w.get('name', ''), 'url': w.get('url', ''), 'isDefault': w.get('isDefault', False)} for w in watch],
                    'downloadServers': [{'name': d.get('name', ''), 'url': d.get('url', '')} for d in download],
                }
                ep_list.append(entry)
            ep_list.sort(key=lambda e: e['episodeNumber'])
            seasons_out.append({'seasonNumber': snum, 'episodes': ep_list})
        seasons_out.sort(key=lambda x: x['seasonNumber'])
        genres = s.get('genres', [])
        if not genres and s.get('categories'):
            genres = s['categories']
        item = {
            'title': title,
            'year': s.get('year', ''),
            'rating': s.get('rating', ''),
            'type': '\u0623\u062c\u0646\u0628\u064a',
            'contentType': 'series',
            'description': s.get('description', ''),
            'cast': s.get('cast', []),
            'poster': s.get('poster', ''),
            'categories': genres,
            'quality': s.get('quality', ''),
            'isComplete': False,
            'seasons': seasons_out,
        }
        out.append(item)
    out.sort(key=lambda x: x['title'].strip())
    return out

def save_site_format(data_list, output_path=None):
    if output_path is None:
        output_path = os.path.join(SCRIPT_DIR, 'data_foreign_series.js')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'// مسلسلات أجنبية من tuktukhd — {len(data_list)} مسلسل\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('const cd_foreign_series = ')
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    p(f'📁 تم الحفظ: {output_path} ({len(data_list)} مسلسل)')
    return output_path


# ===== \u062f\u0645\u062c \u0645\u0639 \u0645\u0644\u0641 \u062d\u0627\u0644\u064a =====
def merge_with_existing(new_series, existing_path):
    if not os.path.exists(existing_path):
        p(f'\u26a0 \u0627\u0644\u0645\u0644\u0641 \u0627\u0644\u062d\u0627\u0644\u064a \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f: {existing_path}')
        return new_series
    with open(existing_path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'(?:const|let|var)\s+\w+\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
    if not m:
        p('\u274c \u0644\u0645 \u064a\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0645\u0635\u0641\u0648\u0641\u0629 \u0641\u064a \u0627\u0644\u0645\u0644\u0641')
        return new_series
    existing = json.loads(m.group(1))
    p(f'\U0001f4c2 \u062a\u062d\u0645\u064a\u0644 {len(existing)} \u0639\u0646\u0635\u0631 \u0645\u0646 \u0627\u0644\u0645\u0644\u0641 \u0627\u0644\u062d\u0627\u0644\u064a')
    norm = lambda t: re.sub(r'\s+', '', (t or '').strip()).lower()
    exist_titles = {norm(x.get('title', '')): x for x in existing}
    added = 0
    updated = 0
    for item in new_series:
        t = norm(item.get('title', ''))
        if t in exist_titles:
            old = exist_titles[t]
            changed = False
            for key in ('rating', 'quality', 'description', 'poster', 'cast', 'categories'):
                if key in item and item[key] != old.get(key):
                    old[key] = item[key]
                    changed = True
            if 'seasons' in item and item['seasons']:
                old_seasons = {s.get('seasonNumber', 0): s for s in old.get('seasons', [])}
                for s in item['seasons']:
                    sn = s.get('seasonNumber', 0)
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
    p(f'\u2705 \u062c\u062f\u064a\u062f: {added} | \u0645\u062d\u062f\u062b: {updated} | \u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a: {len(existing)}')
    return existing


# ===== MAIN =====
def main():
    parser = argparse.ArgumentParser(description='\u0633\u0643\u0631\u0628\u062a \u0633\u062d\u0628 \u0645\u0633\u0644\u0633\u0644\u0627\u062a \u0623\u062c\u0646\u0628\u064a\u0629 \u0645\u0646 tuktukhd')
    parser.add_argument('--start', type=int, default=1, help='\u0635\u0641\u062d\u0629 \u0627\u0644\u0628\u062f\u0627\u064a\u0629 (\u0627\u0641\u062a\u0631\u0627\u0636\u064a: 1)')
    parser.add_argument('--end', type=int, default=1, help='\u0635\u0641\u062d\u0629 \u0627\u0644\u0646\u0647\u0627\u064a\u0629 (\u0627\u0641\u062a\u0631\u0627\u0636\u064a: 1)')
    parser.add_argument('--workers', type=int, default=4, help='\u0639\u062f\u062f \u0627\u0644\u0639\u0645\u0627\u0644 (\u0627\u0641\u062a\u0631\u0627\u0636\u064a: 4)')
    parser.add_argument('--phase', choices=['all', 'listing', 'detail', 'seasons', 'servers'], default='all', help='\u0627\u0644\u0645\u0631\u062d\u0644\u0629')
    parser.add_argument('--resume', action='store_true', help='\u0627\u0633\u062a\u0626\u0646\u0627\u0641 \u0645\u0646 \u0627\u0644\u0646\u062a\u0627\u0626\u062c \u0627\u0644\u0633\u0627\u0628\u0642\u0629')
    parser.add_argument('--convert', action='store_true', help='\u062a\u062d\u0648\u064a\u0644 \u0646\u062a\u0627\u0626\u062c JSON \u0625\u0644\u0649 \u0635\u064a\u063a\u0629 \u0627\u0644\u0645\u0648\u0642\u0639 \u0641\u0642\u0637')
    parser.add_argument('--merge', type=str, default='', help='\u062f\u0645\u062c \u0645\u0639 \u0645\u0644\u0641 \u062d\u0627\u0644\u064a')
    parser.add_argument('--output', type=str, default='', help='\u0645\u0644\u0641 \u0627\u0644\u0625\u062e\u0631\u0627\u062c')
    args = parser.parse_args()

    p('=' * 55)
    p(f'\U0001f4fa \u0633\u062d\u0628 \u0645\u0633\u0644\u0633\u0644\u0627\u062a \u0623\u062c\u0646\u0628\u064a\u0629 \u0645\u0646 tuktukhd - \u0635\u0641\u062d\u0627\u062a {args.start}-{args.end}')
    p(f'   \u0639\u0645\u0627\u0644: {args.workers} | \u0645\u0631\u062d\u0644\u0629: {args.phase}')
    p('=' * 55)

    if args.convert:
        path = os.path.join(DATA_DIR, 'foreign_series_full.json')
        if not os.path.exists(path):
            path = os.path.join(DATA_DIR, 'foreign_series_detail.json')
        if not os.path.exists(path):
            p(f'\u274c \u0627\u0644\u0645\u0644\u0641 \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f: foreign_series_full.json / foreign_series_detail.json')
            return
        series = load_json(path)
        p(f'\U0001f4c2 \u062a\u062d\u0645\u064a\u0644 {len(series)} \u0645\u0633\u0644\u0633\u0644 \u0645\u0646 {path}')
        converted = to_site_format(series)
        output = args.output if args.output else os.path.join(SCRIPT_DIR, 'data_foreign_series.js')
        if args.merge:
            merged = merge_with_existing(converted, args.merge)
            var_name = os.path.basename(args.merge).replace('.js', '').replace('data-', 'cd_').replace('-', '_')
            with open(output, 'w', encoding='utf-8') as f:
                f.write(f'// \u0645\u0633\u0644\u0633\u0644\u0627\u062a \u0623\u062c\u0646\u0628\u064a\u0629 \u2014 {len(merged)} \u0645\u0633\u0644\u0633\u0644 (\u0628\u0639\u062f \u0627\u0644\u062f\u0645\u062c)\n')
                f.write(f'// \u062a\u0645 \u0627\u0644\u062a\u0648\u0644\u064a\u062f: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'const {var_name} = ')
                json.dump(merged, f, ensure_ascii=False, indent=2)
            p(f'\U0001f4c1 \u062a\u0645 \u062d\u0641\u0638 \u0627\u0644\u062f\u0645\u062c: {output} ({len(merged)} \u0645\u0633\u0644\u0633\u0644)')
        else:
            save_site_format(converted, output)
        return

    if args.phase in ('seasons', 'servers', 'all'):
        load_path = os.path.join(DATA_DIR, 'foreign_series_full.json')
        if args.resume and os.path.exists(load_path):
            series = load_json(load_path)
            p(f'\U0001f4c2 \u062a\u062d\u0645\u064a\u0644 {len(series)} \u0645\u0633\u0644\u0633\u0644 \u0645\u0646 {load_path}')
        else:
            series = None
    else:
        series = None

    if series is None and args.phase in ('all', 'listing'):
        p('\n=== \u0627\u0644\u0645\u0631\u062d\u0644\u0629 1: \u0627\u0644\u0642\u0627\u0626\u0645\u0629 ===')
        items = run_listing(args.start, args.end, args.workers, resume=args.resume)
        series = items
        save_json(os.path.join(DATA_DIR, 'foreign_series_full.json'), series)
    elif series is None:
        for fname in ['foreign_series_full.json', 'foreign_series_detail.json', 'foreign_series_listing.json']:
            fp = os.path.join(DATA_DIR, fname)
            if os.path.exists(fp):
                series = load_json(fp)
                p(f'\U0001f4c2 \u062a\u062d\u0645\u064a\u0644 {fname}: {len(series)} \u0639\u0646\u0635\u0631')
                break
        else:
            p('\u274c \u0644\u0627 \u062a\u0648\u062c\u062f \u0628\u064a\u0627\u0646\u0627\u062a. \u0634\u063a\u0651\u0644 --phase listing \u0623\u0648\u0644\u0627\u064b')
            return

    if args.phase in ('all', 'detail'):
        p('\n=== \u0627\u0644\u0645\u0631\u062d\u0644\u0629 2: \u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0645\u0633\u0644\u0633\u0644\u0627\u062a ===')
        series = run_detail(series, args.workers, resume=args.resume)

    if args.phase in ('all', 'seasons'):
        p('\n=== \u0627\u0644\u0645\u0631\u062d\u0644\u0629 3: \u062d\u0644\u0642\u0627\u062a \u0627\u0644\u0645\u0648\u0627\u0633\u0645 ===')
        series = run_seasons(series, args.workers, resume=args.resume)

    if args.phase in ('all', 'servers'):
        p('\n=== \u0627\u0644\u0645\u0631\u062d\u0644\u0629 4: \u0627\u0644\u0633\u064a\u0631\u0641\u0631\u0627\u062a ===')
        series = run_servers(series, args.workers, resume=args.resume)

    final_path = os.path.join(DATA_DIR, 'foreign_series_full.json')
    save_json(final_path, series)
    total_eps = sum(len(s.get('episodes', [])) for s in series)
    total_srv = sum(
        sum(len(ep.get('servers', {}).get('watch', [])) for ep in s.get('episodes', []))
        for s in series
    )
    p(f'\n\u2705 \u062a\u0645: {len(series)} \u0645\u0633\u0644\u0633\u0644, {total_eps} \u062d\u0644\u0642\u0629, {total_srv} \u0633\u064a\u0631\u0641\u0631')
    p(f'\U0001f4c1 {final_path}')

    converted = to_site_format(series)
    output = args.output if args.output else os.path.join(SCRIPT_DIR, 'data_foreign_series.js')
    if args.merge:
        merged = merge_with_existing(converted, args.merge)
        var_name = os.path.basename(args.merge).replace('.js', '').replace('data-', 'cd_')
        with open(output, 'w', encoding='utf-8') as f:
            f.write(f'// \u0645\u0633\u0644\u0633\u0644\u0627\u062a \u0623\u062c\u0646\u0628\u064a\u0629 \u2014 {len(merged)} \u0645\u0633\u0644\u0633\u0644 (\u0628\u0639\u062f \u0627\u0644\u062f\u0645\u062c)\n')
            f.write(f'// \u062a\u0645 \u0627\u0644\u062a\u0648\u0644\u064a\u062f: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'const {var_name} = ')
            json.dump(merged, f, ensure_ascii=False, indent=2)
        p(f'\U0001f4c1 \u062a\u0645 \u062d\u0641\u0638 \u0627\u0644\u062f\u0645\u062c: {output}')
    else:
        save_site_format(converted, output)


if __name__ == '__main__':
    main()
