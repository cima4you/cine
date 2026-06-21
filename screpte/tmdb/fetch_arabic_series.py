#!/usr/bin/env python3
"""
سحب مسلسلات عربية من TMDb حسب السنة (2020-2026)
Two-phase:
  1. Discover all series by year
  2. Fetch Arabic translations in parallel
يحفظ في scripts/tmdb/data/ حسب السنة

Usage:
  python scripts/tmdb/fetch_arabic_series.py
"""
import requests, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

TMDB_KEY = "0301bf9dd3a630dcbbea37f5c2b07d3e"
BASE = "https://api.themoviedb.org/3"
HEADERS = {"Accept": "application/json"}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def tmdb_get(url, params, retries=3):
    params["api_key"] = TMDB_KEY
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=15)
            if r.status_code == 429:
                time.sleep(5)
                continue
            r.raise_for_status()
            return r.json()
        except:
            if attempt == retries - 1:
                return None
            time.sleep(2)
    return None

def fetch_discover_page(year, page):
    """Fetch one discover page."""
    data = tmdb_get(f"{BASE}/discover/tv", {
        "first_air_date_year": year,
        "with_original_language": "ar",
        "sort_by": "popularity.desc",
        "page": page,
    })
    if not data or not data.get("results"):
        return year, page, [], 0
    return year, page, data["results"], data.get("total_pages", 1)

def fetch_translations(tmdb_id, delay=0):
    """Fetch Arabic translation for a series."""
    time.sleep(delay)
    data = tmdb_get(f"{BASE}/tv/{tmdb_id}", {"language": "ar"})
    if not data:
        return tmdb_id, "", "", {}, "", 0, 0
    # Get Arabic translation
    ar_name = data.get("original_name", "") or data.get("name", "")
    ar_overview = data.get("overview", "")
    return tmdb_id, ar_name, ar_overview, {
        "genres": [g["name"] for g in data.get("genres", [])],
        "networks": [n["name"] for n in data.get("networks", [])],
        "origin_country": data.get("origin_country", []),
        "seasons_count": data.get("number_of_seasons", 0),
        "episodes_count": data.get("number_of_episodes", 0),
        "status": data.get("status", ""),
    }, data.get("first_air_date", ""), data.get("vote_average", 0), data.get("poster_path", "")

def main():
    YEARS = list(range(2020, 2027))

    # Phase 1: Discover all series
    all_raw = {y: [] for y in YEARS}
    print('=== Phase 1: Discovering series ===')
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = []
        for year in YEARS:
            # First get page count
            d = tmdb_get(f"{BASE}/discover/tv", {
                "first_air_date_year": year,
                "with_original_language": "ar",
                "page": 1,
            })
            total_pages = d.get("total_pages", 1) if d else 1
            print(f'{year}: {d.get("total_results", 0)} series, {total_pages} pages')
            for p in range(1, total_pages + 1):
                futures.append(ex.submit(fetch_discover_page, year, p))
            time.sleep(0.3)

        for fut in as_completed(futures):
            year, page, results, total = fut.result()
            all_raw[year].extend(results)

    total_discovered = sum(len(v) for v in all_raw.values())
    print(f'\nTotal discovered: {total_discovered}')
    for y in YEARS:
        print(f'  {y}: {len(all_raw[y])}')

    # Phase 2: Fetch details in parallel
    print('\n=== Phase 2: Fetching Arabic details ===')
    detail_map = {}
    all_vids = []
    for year in YEARS:
        for s in all_raw[year]:
            all_vids.append((year, s["id"]))

    def fetch_detail(year, vid):
        result = fetch_translations(vid, delay=0)
        return year, vid, result

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(fetch_detail, year, vid): (year, vid) for year, vid in all_vids}
        done = 0
        for fut in as_completed(futures):
            year, vid = futures[fut]
            try:
                y, v, (tmdb_id, ar_name, ar_overview, detail, first_air_date, rating, poster_path) = fut.result(timeout=30)
                if tmdb_id:
                    detail_map[(year, vid)] = {
                        "ar_name": ar_name,
                        "ar_overview": ar_overview,
                        "detail": detail,
                        "first_air_date": first_air_date,
                        "rating": rating,
                        "poster_path": poster_path,
                    }
            except:
                pass
            done += 1
            if done % 100 == 0:
                print(f'  Details: {done}/{len(all_vids)}')

    # Phase 3: Build output
    print('\n=== Phase 3: Building output ===')
    for year in YEARS:
        output = []
        for s in all_raw[year]:
            key = (year, s["id"])
            d = detail_map.get(key, {})
            detail = d.get("detail", {})
            poster = f"https://image.tmdb.org/t/p/w500{d['poster_path']}" if d.get("poster_path") else ""
            if not poster:
                poster = f"https://image.tmdb.org/t/p/w500{s['poster_path']}" if s.get("poster_path") else ""

            item = {
                "tmdb_id": s["id"],
                "title": d.get("ar_name") or s.get("original_name") or s.get("name", ""),
                "title_en": s.get("name", ""),
                "year": year,
                "first_air_date": d.get("first_air_date") or s.get("first_air_date", ""),
                "overview": s.get("overview", ""),
                "arabic_overview": d.get("ar_overview", ""),
                "rating": d.get("rating") or s.get("vote_average", 0),
                "poster": poster,
                "genres": detail.get("genres", []),
                "networks": detail.get("networks", []),
                "origin_country": detail.get("origin_country", []),
                "seasons_count": detail.get("seasons_count", 0),
                "episodes_count": detail.get("episodes_count", 0),
                "status": detail.get("status", ""),
            }
            output.append(item)

        outpath = os.path.join(DATA_DIR, f'arabic_series_{year}.json')
        with open(outpath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f'{year}: {len(output)} series -> {outpath}')

    # Combined
    combined = []
    for year in YEARS:
        with open(os.path.join(DATA_DIR, f'arabic_series_{year}.json'), 'r', encoding='utf-8') as f:
            combined.extend(json.load(f))
    outpath = os.path.join(DATA_DIR, 'arabic_series_all.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f'\nCombined: {len(combined)} series -> {outpath}')

if __name__ == '__main__':
    main()
