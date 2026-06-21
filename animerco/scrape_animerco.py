#!/usr/bin/env python3
"""
Animerco Scraper v2 - scrapes movies AND series from eta.animerco.org
Movies: detail info + all server URLs (via AJAX)
Series: detail info + seasons + episodes + server URLs (via AJAX, limited per episode)

Usage:
    python scrape_animerco.py --start 1 --end 5
    python scrape_animerco.py --animes --start 1 --end 3
    python scrape_animerco.py --animes --max-series 5   # limit deep scrape
    python scrape_animerco.py --animes --episode-servers 3   # servers per episode
"""

import requests
import re
import json
import os
import argparse
import concurrent.futures
import sys
import io
import time
import html as html_mod
from urllib.parse import urljoin

# Make stdout UTF-8-safe so Arabic output doesn't crash Windows consoles
if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_URL = "https://eta.animerco.org"
AJAX_URL = urljoin(BASE_URL, "/wp-admin/admin-ajax.php")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

TYPE_LABEL = {
    'movie': '\u0623\u0646\u0645\u064a',
    'tv': '\u0623\u0646\u0645\u064a',
    'ova': '\u0623\u0646\u0645\u064a',
}

CONTENT_TYPE = {
    'movie': 'movie',
    'tv': 'series',
    'ova': 'movie',
}


def safe_print(*args, **kwargs):
    """Print without crashing on Unicode encoding errors."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        msg = ' '.join(str(a) for a in args)
        print(msg.encode('ascii', 'replace').decode('ascii'), **kwargs)


def clean_html_entities(text):
    text = html_mod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch(url, timeout=30):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.encoding = 'utf-8'
        return r.text
    except Exception as e:
        print(f"  [!] Error fetching {url}: {e}", file=sys.stderr)
        return ''


def fetch_pages_count(html):
    pages = re.findall(r'/\w+/page/(\d+)/', html)
    if pages:
        return max(int(p) for p in pages)
    nums = re.findall(r'<a[^>]*>(\d+)</a>', html)
    nums = [int(n) for n in nums if n.isdigit() and int(n) < 1000]
    if nums:
        return max(nums)
    return 1


def scrape_listing_page(url):
    """Scrape a single listing page and return movie/anime entries."""
    html = fetch(url)
    if not html:
        return []

    items = []
    blocks = re.findall(
        r'<div class="box-5x1 media-block"[^>]*id="post-(\d+)"[^>]*>'
        r'\s*<div class="anime-card">(.*?)</div>\s*</div>',
        html, re.DOTALL
    )

    for post_id, block in blocks:
        title_m = re.search(r'<h3>(.*?)</h3>', block)
        if not title_m:
            continue
        title = clean_html_entities(title_m.group(1))

        url_m = re.search(r'<a href="(https://[^"]+)"', block)
        detail_url = url_m.group(1) if url_m else ''

        poster_m = re.search(r'data-src="(https://[^"]+)"', block)
        poster = poster_m.group(1) if poster_m else ''

        year_m = re.search(
            r'<span class="anime-aired">\s*(\d{4})\s*</span>', block
        )
        year = year_m.group(1) if year_m else ''

        rating_m = re.search(
            r'class="rating"[^>]*>.*?'
            r'<span>\u0627\u0644\u062a\u0642\u064a\u064a\u0645</span>\s*([\d.]+)',
            block, re.DOTALL
        )
        rating = rating_m.group(1) if rating_m else ''

        type_m = re.search(
            r'<span class="anime-type">(.*?)</span>', block
        )
        ptype = type_m.group(1).strip().lower() if type_m else 'movie'

        items.append({
            'post_id': post_id,
            'title': title,
            'url': detail_url,
            'poster': poster,
            'year': year,
            'rating': rating,
            'contentType': CONTENT_TYPE.get(ptype, 'movie'),
        })

    pnum = re.search(r'/page/(\d+)/', url)
    page_label = pnum.group(1) if pnum else '1'
    print(f"  [>] Page {page_label}: {len(items)} items")
    return items


def extract_nonce(html):
    nm = re.search(
        r'var dtAjax\s*=\s*{.*?"security":"([^"]+)"', html, re.DOTALL
    )
    return nm.group(1) if nm else ''


def ajax_fetch_embed(post_id, nume, nonce, ajax_type):
    """Fetch embed URL via AJAX. Returns URL string or empty string on failure."""
    try:
        r = requests.post(AJAX_URL, data={
            'action': 'player_ajax',
            'security': nonce,
            'post': post_id,
            'nume': str(nume),
            'type': ajax_type,
        }, headers=HEADERS, timeout=15)
        data = r.json()
        return data.get('embed_url', '')
    except Exception as e:
        return ''


def resolve_iframe(embed_url, referer):
    """Fetch the JW Player proxy page and extract the iframe src.
    Returns the iframe URL, or the embed_url itself if no iframe found."""
    if not embed_url:
        return ''
    try:
        h = dict(HEADERS)
        if referer:
            h['Referer'] = referer
        r = requests.get(embed_url, headers=h, timeout=15, allow_redirects=True)
        m = re.search(r'<iframe[^>]*src="([^"]+)"', r.text)
        if m:
            return html_mod.unescape(m.group(1))
        return embed_url
    except Exception:
        return embed_url


def extract_server_buttons(html):
    """Extract server button info (type, post, nume, nonce, name) from detail/episode page HTML."""
    servers = []
    pattern = r"<a[^>]*?data-type=['\"]([^'\"]+)['\"][^>]*?data-post=['\"]([^'\"]+)['\"][^>]*?data-nume=['\"]([^'\"]+)['\"][^>]*?data-nonce=['\"]([^'\"]+)['\"][^>]*?>.*?<span[^>]*class=['\"]server['\"][^>]*>([^<]+)</span>"
    for m in re.finditer(pattern, html, re.DOTALL):
        servers.append({
            'type': m.group(1),
            'post': m.group(2),
            'nume': m.group(3),
            'nonce': m.group(4),
            'name': m.group(5).strip(),
        })
    return servers


def extract_detail(item, max_episode_servers=5):
    """Scrape detail page for additional info.
    For movies: also fetch all server URLs via AJAX.
    For series: also scrape seasons, episodes, and server URLs.
    """
    if not item.get('url'):
        return item

    html = fetch(item['url'])
    if not html:
        return item

    result = dict(item)
    result['description'] = ''
    desc_m = re.search(
        r'<div class="content">\s*<p>(.*?)</p>', html, re.DOTALL
    )
    if desc_m:
        result['description'] = clean_html_entities(
            re.sub(r'<[^>]+>', '', desc_m.group(1))
        )

    genres_m = re.findall(
        r'<a href="[^"]*genre/[^"]*"[^>]*class="badge[^"]*"[^>]*>(.*?)</a>',
        html
    )
    result['categories'] = [g.strip() for g in genres_m if g.strip()]

    result['year'] = item.get('year', '')
    year_m = re.search(r'<a href="[^"]*release/(\d{4})/"', html)
    if year_m:
        result['year'] = year_m.group(1)

    result['duration'] = ''
    dur_m = re.search(r'(\d[\d\s]*\u062f\u0642\u064a\u0642\u0629)', html)
    if dur_m:
        result['duration'] = dur_m.group(1).strip()

    result['quality'] = ''
    qual_m = re.search(
        r'<a href="[^"]*quality/[^"]*"[^>]*>(.*?)</a>', html
    )
    if qual_m:
        result['quality'] = qual_m.group(1).strip()

    result['type'] = TYPE_LABEL.get('movie', '\u0623\u0646\u0645\u064a')

    if item.get('contentType') == 'series':
        result['servers'] = []
        result['seasons'] = scrape_seasons(item, html, max_episode_servers)
    else:
        result['servers'] = scrape_movie_servers(html, item['post_id'])

    return result


def scrape_movie_servers(html, post_id):
    """Extract movie server buttons and resolve to actual iframe URLs."""
    buttons = extract_server_buttons(html)
    if not buttons:
        return []

    servers = []
    for i, btn in enumerate(buttons):
        embed_url = ajax_fetch_embed(btn['post'], btn['nume'], btn['nonce'], 'movie')
        iframe_url = resolve_iframe(embed_url, '')
        servers.append({'name': btn['name'], 'url': iframe_url})
        if iframe_url:
            print(f"    [OK] Server {i+1}/{len(buttons)}: {btn['name']}")
        else:
            print(f"    [!] Server {i+1}/{len(buttons)}: {btn['name']} - no URL")
        time.sleep(0.15)

    return servers


def scrape_seasons(anime, detail_html, max_episode_servers=5):
    """Extract seasons from anime detail page, then scrape episodes + servers."""
    seasons = []
    title = anime.get('title', '')

    season_links = re.findall(
        r"<a href='(https://[^']+/seasons/[^']+)'[^>]*>"
        r"\s*<h3>(.*?)</h3>",
        detail_html
    )

    if not season_links:
        print(f"  [!] {title}: No season links found")
        return []

    print(f"  [~] {title}: {len(season_links)} season(s) found")
    for season_url, season_name_html in season_links:
        season_name = clean_html_entities(re.sub(r'<[^>]+>', '', season_name_html))
        season_num_m = re.search(r'season-(\d+)', season_url)
        season_num = int(season_num_m.group(1)) if season_num_m else 1

        episodes = scrape_episodes(season_url, max_episode_servers)
        print(f"    [>] Season {season_num}: {len(episodes)} episodes")

        seasons.append({
            'season_number': season_num,
            'name': season_name,
            'url': season_url,
            'episodes': episodes,
        })

    return seasons


def scrape_episodes(season_url, max_episode_servers=5):
    """Scrape a season page for episode list, then each episode for servers."""
    html = fetch(season_url)
    if not html:
        return []

    episodes = []

    ep_blocks = re.findall(
        r"<li data-number='(\d+)'>"
        r"<a href='(https://[^']+/episodes/[^']+)'[^>]*>"
        r".*?data-src='([^']*)'",
        html
    )

    if not ep_blocks:
        ep_blocks = re.findall(
            r"<li data-number='(\d+)'>.*?"
            r"href='(https://[^']+/episodes/[^']+)'",
            html
        )
        for ep_num, ep_url in ep_blocks:
            ep_title = f"\u0627\u0644\u062d\u0644\u0642\u0629 {ep_num}"
            episodes.append({
                'number': int(ep_num),
                'title': ep_title,
                'url': ep_url,
                'poster': '',
                'servers': [],
            })
    else:
        for ep_num, ep_url, poster in ep_blocks:
            ep_title = f"\u0627\u0644\u062d\u0644\u0642\u0629 {ep_num}"
            episodes.append({
                'number': int(ep_num),
                'title': ep_title,
                'url': ep_url,
                'poster': poster,
                'servers': [],
            })

    for ep in episodes:
        servers = scrape_episode_servers(ep['url'], max_episode_servers)
        ep['servers'] = servers

    return episodes


def scrape_episode_servers(episode_url, max_servers=5):
    """Scrape an episode page for server buttons and resolve to actual iframe URLs."""
    html = fetch(episode_url)
    if not html:
        return []

    buttons = extract_server_buttons(html)
    servers = []
    for i, btn in enumerate(buttons):
        if i >= max_servers:
            break
        embed_url = ajax_fetch_embed(btn['post'], btn['nume'], btn['nonce'], 'tv')
        iframe_url = resolve_iframe(embed_url, episode_url)
        servers.append({'name': btn['name'], 'url': iframe_url})
        if iframe_url:
            print(f"      [OK] {btn['name']}")
        else:
            print(f"      [!] {btn['name']} - no URL")
        time.sleep(0.15)

    return servers


def save_results(all_items, filename='results_animerco_movies.json'):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print(f"\n  [OK] Saved {len(all_items)} items to {filepath}")


def main():
    parser = argparse.ArgumentParser(description='Animerco Scraper v2')
    parser.add_argument('--start', type=int, default=1, help='Start page')
    parser.add_argument('--end', type=int, default=0, help='End page (0 = auto)')
    parser.add_argument('--workers', type=int, default=5, help='Thread workers')
    parser.add_argument('--no-details', action='store_true', help='Listing only')
    parser.add_argument('--animes', action='store_true', help='Scrape animes')
    parser.add_argument('--episode-servers', type=int, default=5,
                        help='Max servers per episode (series only)')
    parser.add_argument('--max-series', type=int, default=0,
                        help='Max series to deep-scrape (0 = all)')
    args = parser.parse_args()

    section = 'animes' if args.animes else 'movies'
    section_label = 'Animes' if args.animes else 'Movies'
    list_url = f"{BASE_URL}/{section}/"
    filename = f'results_animerco_{section}.json'

    print(f"[*] Animerco Scraper v2 - {section_label}")
    print(f"[*] Pages: {args.start} to {'auto' if args.end == 0 else args.end}")

    first_page_html = fetch(list_url)
    if not first_page_html:
        print("[!] Cannot access site", file=sys.stderr)
        sys.exit(1)

    total_pages = fetch_pages_count(first_page_html)
    if args.end == 0:
        args.end = total_pages
    end_page = min(args.end, total_pages)
    print(f"[*] Total pages: {total_pages}, scraping: {args.start}-{end_page}")

    all_listings = []
    for page in range(args.start, end_page + 1):
        url = list_url if page == 1 else f"{BASE_URL}/{section}/page/{page}/"
        items = scrape_listing_page(url)
        all_listings.extend(items)

    print(f"\n[*] Total listings: {len(all_listings)}")

    results = all_listings
    if not args.no_details:
        deep_limit = args.max_series if args.max_series > 0 else len(all_listings)
        print(f"[*] Deep-scraping up to {deep_limit} items...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            future_map = {}
            for i, m in enumerate(all_listings):
                if i >= deep_limit:
                    print(f"  [!] Skipping #{i+1} (max-series limit)")
                    break
                future = ex.submit(
                    extract_detail, m, args.episode_servers
                )
                future_map[future] = m

            results = []
            done = 0
            for future in concurrent.futures.as_completed(future_map):
                done += 1
                try:
                    r = future.result()
                    if r:
                        results.append(r)
                        label = r.get('title', '?')
                        eps = ''
                        if r.get('contentType') == 'series':
                            s_count = len(r.get('seasons', []))
                            e_count = sum(
                                len(s.get('episodes', []))
                                for s in r.get('seasons', [])
                            )
                            eps = f' [{s_count}s/{e_count}e]'
                        print(f"  [{done}/{deep_limit}] {label}{eps}")
                except Exception as e:
                    print(f"  [!] Error: {e}", file=sys.stderr)

    print(f"\n[*] Done! Collected {len(results)} {section_label.lower()}")

    save_results(results, filename)

    counts = {}
    for r in results:
        y = r.get('year', 'unknown')
        counts[y] = counts.get(y, 0) + 1
    print(f"\n[*] By year: {dict(sorted(counts.items(), reverse=True))}")


if __name__ == '__main__':
    main()
