import json, re, os, sys, time
import requests

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

OMDB_KEY = 'dac33e2a'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def get_top250_list():
    r = requests.get(
        'https://raw.githubusercontent.com/Devanshi1206/IMDb-Top-250-Movies/main/PopularMovies.csv',
        headers=HEADERS, timeout=15
    )
    r.encoding = 'utf-8'
    movies = []
    for line in r.text.split('\n')[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) < 5:
            continue
        link = parts[4].strip()
        m = re.search(r'tt\d+', link)
        if not m:
            continue
        imdb_id = m.group(0)
        title = parts[1].strip().strip('"')
        rating = parts[2].strip()
        year = parts[3].strip()
        movies.append({'imdb_id': imdb_id, 'title': title, 'rating': rating, 'year': year})
    return movies

def get_omdb_details(imdb_id):
    try:
        r = requests.get('http://www.omdbapi.com/', params={
            'i': imdb_id, 'apikey': OMDB_KEY, 'plot': 'short'
        }, timeout=10)
        data = r.json()
        if data.get('Response') == 'True':
            return {
                'title': data.get('Title', ''),
                'year': data.get('Year', ''),
                'rated': data.get('Rated', ''),
                'runtime': data.get('Runtime', ''),
                'genre': data.get('Genre', ''),
                'director': data.get('Director', ''),
                'actors': data.get('Actors', ''),
                'plot': data.get('Plot', ''),
                'poster': data.get('Poster', ''),
                'imdb_rating': data.get('imdbRating', ''),
                'metascore': data.get('Metascore', ''),
                'imdb_votes': data.get('imdbVotes', ''),
                'type': data.get('Type', ''),
            }
    except Exception as e:
        print(f'    OMDb error: {e}')
    return None

def get_stream_server(imdb_id):
    url = f'https://streamimdb.ru/embed/movie/{imdb_id}'
    return {
        'watch_server': 'streamimdb.ru',
        'watch_server_url': url,
    }

def load_existing(output_path):
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def main():
    limit = 0
    resume = False
    args = sys.argv[1:]
    while args:
        if args[0] == '--limit' and len(args) > 1:
            limit = int(args[1])
            args = args[2:]
        elif args[0] == '--resume':
            resume = True
            args = args[1:]
        else:
            args = args[1:]

    output_path = os.path.join(OUTPUT_DIR, 'top250.json')

    print('Fetching IMDb Top 250 list...')
    all_movies = get_top250_list()
    if limit > 0:
        all_movies = all_movies[:limit]
    print(f'Found {len(all_movies)} movies\n')

    results = load_existing(output_path) if resume else []
    existing_ids = {r['imdb_id'] for r in results}
    if existing_ids:
        print(f'Resuming: {len(results)} already processed\n')

    for i, m in enumerate(all_movies, 1):
        imdb_id = m['imdb_id']
        if imdb_id in existing_ids:
            print(f'[{i}/{len(all_movies)}] {m["title"]} ({imdb_id}) - skipped')
            continue

        print(f'[{i}/{len(all_movies)}] {m["title"]} ({imdb_id})')

        details = get_omdb_details(imdb_id)
        if details:
            m.update(details)
            print(f'    OMDb: {details.get("title","")} ({details.get("year","")})')
        else:
            print(f'    OMDb: skipped')

        time.sleep(0.2)

        servers = get_stream_server(imdb_id)
        m.update(servers)
        print(f'    Server: {servers["watch_server"]}')

        results.append(m)

        if i % 25 == 0:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f'    [Checkpoint saved: {len(results)} movies]')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with_servers = sum(1 for r in results if r.get('watch_server_url'))
    print(f'\nSaved {len(results)} movies to {output_path}')
    print(f'Movies with servers: {with_servers}/{len(results)}')

if __name__ == '__main__':
    main()
