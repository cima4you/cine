import re, json, time, requests, sys

TMDB_KEY = "0301bf9dd3a630dcbbea37f5c2b07d3e"
TMDB_SEARCH = "https://api.themoviedb.org/3/search/movie"
TMDB_MOVIE_VIDEOS = "https://api.themoviedb.org/3/movie/{}/videos"
TMDB_TV_VIDEOS = "https://api.themoviedb.org/3/tv/{}/videos"
DATA_FILE = r"D:\Users\DT01\Desktop\rachid-site\data.js"

headers = {"Accept": "application/json"}

def tmdb_get(url, params):
    params["api_key"] = TMDB_KEY
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            if r.status_code == 429:
                print("  [ratelimited, waiting 5s]", flush=True)
                time.sleep(5)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  [error: {e}, retry {attempt+1}]", flush=True)
            time.sleep(2)
    return None

def find_media_trailer(endpoint, videos_endpoint, title, year):
    data = tmdb_get(endpoint, {"query": title, "year": year})
    if not data:
        return None
    results = data.get("results", [])
    if not results:
        data2 = tmdb_get(endpoint, {"query": title})
        if not data2:
            return None
        results = data2.get("results", [])
    if not results:
        return None

    media_id = results[0]["id"]
    videos = tmdb_get(videos_endpoint.format(media_id), {})
    if not videos:
        return None
    for v in videos.get("results", []):
        if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser"):
            return f"https://www.youtube.com/embed/{v['key']}"
    return None

def find_trailer(title, year):
    # Try movie search first
    t = find_media_trailer(TMDB_SEARCH, TMDB_MOVIE_VIDEOS, title, year)
    if t:
        return t
    # Try TV search
    t = find_media_trailer("https://api.themoviedb.org/3/search/tv", TMDB_TV_VIDEOS, title, year)
    if t:
        return t
    # Try removing trailing season number ("Spartacus 1" -> "Spartacus")
    title2 = re.sub(r'\s+\d{1,2}$', '', title).strip()
    if title2 and title2 != title:
        t = find_media_trailer(TMDB_SEARCH, TMDB_MOVIE_VIDEOS, title2, year)
        if t:
            return t
        t = find_media_trailer("https://api.themoviedb.org/3/search/tv", TMDB_TV_VIDEOS, title2, year)
        if t:
            return t
    # Try without year
    t = find_media_trailer(TMDB_SEARCH, TMDB_MOVIE_VIDEOS, title, "")
    if t:
        return t
    t = find_media_trailer("https://api.themoviedb.org/3/search/tv", TMDB_TV_VIDEOS, title, "")
    return t

def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = f.read()

    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1:
        print("Unexpected data.js format")
        return

    prefix = raw[:start]
    suffix = raw[end+1:]
    items = json.loads(raw[start:end+1])
    print(f"Total items: {len(items)}", flush=True)

    foreign_no_trial = [i for i, it in enumerate(items)
                        if it.get("type") == "أجنبي" and not it.get("trial")]
    total = len(foreign_no_trial)
    print(f"Foreign movies without trailer: {total}", flush=True)

    updated = 0
    for seq, idx in enumerate(foreign_no_trial, 1):
        item = items[idx]
        title = item.get("title", "").strip()
        year = item.get("year", "").strip()
        clean = re.sub(r'\s*\d{4}\s*$', '', title).strip()
        if not clean:
            clean = title

        sys.stdout.write(f"[{seq}/{total}] {clean} ({year})... ")
        sys.stdout.flush()
        t = find_trailer(clean, year)
        if t:
            item["trial"] = t
            print("OK", flush=True)
            updated += 1
        else:
            print("not found", flush=True)
        time.sleep(0.3)

    new_raw = prefix + json.dumps(items, ensure_ascii=False) + suffix
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print(f"\nDone. Updated {updated}/{total}", flush=True)

if __name__ == "__main__":
    main()
