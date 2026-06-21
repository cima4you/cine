import json, re, os, sys, time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

BASE_URL = 'https://www.ooanime.com'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
AJAX_HEADERS = {**HEADERS, 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded'}
STATE_PATH = os.path.join(DATA_DIR, 'state.json')
SERIES_PATH = os.path.join(DATA_DIR, 'ooanime_series.json')


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_state(data):
    state = load_state()
    state.update(data)
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = 'utf-8'
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None


def parse_series_list(html):
    series = {}
    for m in re.finditer(r'/series/(\d+)/([^"\'?]+)', html):
        sid, name = m.group(1), unquote(m.group(2))
        series[sid] = name
    return series


def load_initial_series():
    html = fetch(BASE_URL + '/cartoon')
    if not html:
        return {}
    return parse_series_list(html)


def load_more_series(start_id):
    try:
        r = requests.post(BASE_URL + '/load_cartoon.php',
                          data={'id': str(start_id)}, headers=AJAX_HEADERS, timeout=20)
        r.encoding = 'utf-8'
        if r.status_code == 200 and len(r.text) > 100:
            return r.text
    except:
        pass
    return None


def scrape_all_series():
    state = load_state()
    if state.get('series_complete'):
        return load_series_from_file()

    all_series = load_initial_series()
    last_id = 189

    while last_id:
        html = load_more_series(last_id)
        if not html:
            break
        more = parse_series_list(html)
        all_series.update(more)
        buttons = re.findall(r'id="(\d+)"[^>]*class="[^"]*show_more[^"]*"', html)
        last_id = int(buttons[-1]) if buttons else 0

    save_state({'series_complete': True, 'series_count': len(all_series)})
    return all_series


def load_series_from_file():
    if os.path.exists(SERIES_PATH):
        with open(SERIES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {str(s['id']): s for s in data}
    return {}


def scrape_series_detail(sid, sname):
    html = fetch(f'{BASE_URL}/series/{sid}/{sname}')
    if not html:
        return None

    result = {'id': int(sid), 'title': '', 'year': '', 'category': '',
              'language': '', 'country': '', 'rating': '', 'description': '',
              'poster': '', 'seasons': []}

    m = re.search(r'<title>(.*?)</title>', html)
    if m: result['title'] = m.group(1).strip()

    m = re.search(r'<img[^>]*src="([^"]+)"[^>]*style="width:100%', html)
    if m: result['poster'] = m.group(1)

    if not result['poster']:
        m = re.search(r'<div class="movie-img"[^>]*>.*?<img[^>]*src="([^"]+)"', html, re.DOTALL)
        if m: result['poster'] = m.group(1)

    info_section = re.search(r'sec-info">(.*?)(?:<div class="rgt movie-section sec-btn|</div>\s*</div>\s*<div class="row)', html, re.DOTALL)
    if info_section:
        info = info_section.group(1)
        m = re.search(r'سنة الإنتاج\s*:\s*<a[^>]*>([^<]+)', info)
        if m: result['year'] = m.group(1).strip()
        m = re.search(r'التقييم العالمي\s*:\s*<a[^>]*>([\d.]+)', info)
        if m: result['rating'] = m.group(1).strip()
        m = re.search(r'البلد - اللغة\s*:\s*<a[^>]*>([^<]+)', info)
        if m: result['language'] = m.group(1).strip()
        m = re.search(r'البلد - اللغة\s*:\s*<a[^>]*>[^<]+</a>\s*-\s*<a[^>]*>([^<]+)', info)
        if m: result['country'] = m.group(1).strip()
        m = re.search(r'تصنيف المسلسل\s*:\s*<a[^>]*>([^<]+)', info)
        if m: result['category'] = m.group(1).strip()

    m = re.search(r'<div class="movie-story">.*?<div class="movie-title">قصة المسلسل</div>\s*(.*?)\s*</div>', html, re.DOTALL)
    if m:
        story = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        result['description'] = story[:500]

    for sm in re.finditer(r'href="(?:https?://[^/]+)?/seasons/(\d+)/([^"\'?]+)"', html):
        season_id, season_name = sm.group(1), unquote(sm.group(2))
        if season_id not in [str(s['id']) for s in result['seasons']]:
            result['seasons'].append({'id': int(season_id), 'title': season_name, 'episodes': []})

    return result


def scrape_season(season):
    url = f'{BASE_URL}/seasons/{season["id"]}/{season["title"]}'
    html = fetch(url)
    if not html:
        return

    episodes = []
    for m in re.finditer(r'href="(?:https?://[^/]+)?/episode/(\d+)/([^"\'?]+)"[^>]*>', html):
        ep_id, ep_name = m.group(1), unquote(m.group(2))
        if ep_id not in [str(e['id']) for e in episodes]:
            poster = ''
            container = re.search(r'href="(?:https?://[^/]+)?/episode/' + ep_id + r'/[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"', html, re.DOTALL)
            if container:
                poster = container.group(1)
            episodes.append({'id': int(ep_id), 'title': ep_name, 'video_url': '', 'poster': poster})

    season['episodes'] = episodes


def scrape_episode_video(episode):
    url = f'{BASE_URL}/episode/{episode["id"]}/'
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        r.encoding = 'utf-8'
        if r.status_code == 200:
            iframes = re.findall(r'<iframe[^>]*src="([^"]+)"', r.text)
            for iframe in iframes:
                if iframe.endswith('.mp4') or '.mp4' in iframe:
                    episode['video_url'] = iframe
                    break
            if not episode['video_url']:
                videos = re.findall(r'(https?://[^"\']+\.(?:mp4|webm|ogg))', r.text)
                if videos:
                    episode['video_url'] = videos[0]
    except:
        pass


def batch_fetch(func, items, parallel=5):
    results = [None] * len(items)
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        fut_map = {}
        for i, item in enumerate(items):
            fut = pool.submit(func, item)
            fut_map[fut] = i
        for fut in as_completed(fut_map):
            idx = fut_map[fut]
            try:
                results[idx] = fut.result()
            except:
                pass
    return results


def main():
    if '--help' in sys.argv or '-h' in sys.argv:
        print('Usage: python scrape_ooanime.py [options]')
        print('  --series-only       Only scrape series list')
        print('  --seasons-only      Only scrape seasons for series')
        print('  --episodes-only     Only scrape episode videos')
        print('  --resume            Resume from last saved state')
        print('  --from N            Start index (overrides state)')
        print('  --to N              End index')
        print('  --parallel N        Concurrent requests (default 5)')
        return

    series_only = '--series-only' in sys.argv
    seasons_only = '--seasons-only' in sys.argv
    episodes_only = '--episodes-only' in sys.argv
    resume = '--resume' in sys.argv
    parallel = 5
    start_from = 0
    end_to = -1

    args = sys.argv[1:]
    while args:
        if args[0] == '--parallel' and len(args) > 1:
            parallel = int(args[1])
            args = args[2:]
        elif args[0] == '--from' and len(args) > 1:
            start_from = int(args[1])
            args = args[2:]
        elif args[0] == '--to' and len(args) > 1:
            end_to = int(args[1])
            args = args[2:]
        else:
            args = args[1:]

    # Phase 1: Series list
    if not seasons_only and not episodes_only:
        print('=== Phase 1: Scraping series list ===')
        all_series = scrape_all_series()

        series_list = []
        for sid, sname in sorted(all_series.items(), key=lambda x: int(x[0])):
            series_list.append({'id': int(sid), 'title': '', 'year': '', 'category': '',
                                'language': '', 'country': '', 'rating': '', 'description': '',
                                'poster': '', 'name_url': sname, 'seasons': []})

        with open(SERIES_PATH, 'w', encoding='utf-8') as f:
            json.dump(series_list, f, ensure_ascii=False, indent=2)
        print(f'Saved {len(series_list)} series to ooanime_series.json')

        if series_only:
            return

    # Phase 2: Series details + seasons
    if not episodes_only:
        print('\n=== Phase 2: Series details and seasons ===')
        with open(SERIES_PATH, 'r', encoding='utf-8') as f:
            series_list = json.load(f)

        state = load_state()
        last_idx = start_from if start_from > 0 else state.get('series_detail_idx', -1) if resume else -1
        end_idx = end_to if end_to >= 0 else len(series_list)

        to_process = [(i, s) for i, s in enumerate(series_list)
                      if last_idx < i < end_idx and not s.get('seasons')]

        if to_process:
            # Fetch series details concurrently
            items = [(s['id'], s['name_url']) for _, s in to_process]

            def fetch_detail(item):
                sid, sname = item
                return scrape_series_detail(sid, sname)

            results = batch_fetch(fetch_detail, items, parallel)

            for i, s in enumerate([s for _, s in to_process]):
                detail = results[i]
                if detail:
                    s.update({k: v for k, v in detail.items() if k != 'id'})
                    save_state({'series_detail_idx': s['id']})

                if (i + 1) % 10 == 0:
                    with open(SERIES_PATH, 'w', encoding='utf-8') as f:
                        json.dump(series_list, f, ensure_ascii=False, indent=2)

            with open(SERIES_PATH, 'w', encoding='utf-8') as f:
                json.dump(series_list, f, ensure_ascii=False, indent=2)

            has_seasons = sum(1 for s in series_list if s.get('seasons'))
            print(f'Series with seasons: {has_seasons}/{len(series_list)}')

        if seasons_only:
            return

    # Phase 3: Episode videos
    print('\n=== Phase 3: Episode videos ===')
    with open(SERIES_PATH, 'r', encoding='utf-8') as f:
        series_list = json.load(f)

    # Collect all seasons that need episodes scraped
    all_episodes = []
    for s in series_list:
        for season in s.get('seasons', []):
            if not season.get('episodes'):
                all_episodes.append((s['id'], s['name_url'], season))
            else:
                for ep in season.get('episodes', []):
                    if not ep.get('video_url'):
                        all_episodes.append((s['id'], s['name_url'], season, ep))

    state = load_state()
    last_season = start_from if start_from > 0 else state.get('episode_season_idx', -1) if resume else -1

    # First, scrape episode lists for seasons without them
    seasons_no_eps = [(s['id'], s['name_url'], sea) for s in series_list
                      for sea in s.get('seasons', [])
                      if not sea.get('episodes')]

    if seasons_no_eps:
        print(f'Scraping episode lists for {len(seasons_no_eps)} seasons...')

        def fetch_season(item):
            _, _, season = item
            scrape_season(season)
            return season

        batch_fetch(fetch_season, seasons_no_eps, parallel)

        with open(SERIES_PATH, 'w', encoding='utf-8') as f:
            json.dump(series_list, f, ensure_ascii=False, indent=2)

    # Now scrape video URLs for episodes without them
    episodes_no_video = [(s['id'], ep) for s in series_list
                         for sea in s.get('seasons', [])
                         for ep in sea.get('episodes', [])
                         if not ep.get('video_url')]

    if episodes_no_video:
        print(f'Scraping video URLs for {len(episodes_no_video)} episodes...')

        def fetch_video(item):
            _, ep = item
            scrape_episode_video(ep)
            return ep

        batch_fetch(fetch_video, episodes_no_video, parallel)

        with open(SERIES_PATH, 'w', encoding='utf-8') as f:
            json.dump(series_list, f, ensure_ascii=False, indent=2)

    with_video = sum(1 for s in series_list for sea in s.get('seasons', [])
                     for ep in sea.get('episodes', []) if ep.get('video_url'))
    total_eps = sum(1 for s in series_list for sea in s.get('seasons', [])
                    for ep in sea.get('episodes', []))
    print(f'\nTotal: {len(series_list)} series, {total_eps} episodes, {with_video} with video URLs')


if __name__ == '__main__':
    main()
