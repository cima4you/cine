import json
import re
import os
import time
import requests

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
OMDB_API_KEY = 'dac33e2a'
WIKI_HEADERS = {'User-Agent': 'RachidMovies/1.0'}

def load_data_js():
    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    arr_start = content.index('[')
    arr_end = content.rindex(']') + 1
    data = json.loads(content[arr_start:arr_end])
    return data, content[:arr_start], content[arr_end:]

def save_data_js(data, prefix, suffix):
    json_str = json.dumps(data, ensure_ascii=False)
    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)

def clean_title(t):
    t = re.sub(r'[\u0600-\u06FF]+', '', t).strip()
    t = re.sub(r'\s*\d{4}\s*$', '', t).strip()
    return re.sub(r'\s{2,}', ' ', t).strip() or t

def search_wikipedia(title, year):
    q = f'{title} {year} film'
    try:
        r = requests.get('https://en.wikipedia.org/w/api.php',
            params={'action':'query','list':'search','srsearch':q,'format':'json','srlimit':3},
            headers=WIKI_HEADERS, timeout=10)
        for p in r.json().get('query',{}).get('search',[]):
            r2 = requests.get('https://en.wikipedia.org/w/api.php',
                params={'action':'query','titles':p['title'],'prop':'pageprops','format':'json'},
                headers=WIKI_HEADERS, timeout=10)
            for pid, info in r2.json().get('query',{}).get('pages',{}).items():
                wb = info.get('pageprops',{}).get('wikibase_item','')
                if wb and pid != '-1':
                    return wb
    except:
        pass
    return None

def get_imdb_from_wikidata(wid):
    try:
        r = requests.get(f'https://www.wikidata.org/wiki/Special:EntityData/{wid}.json',
            headers=WIKI_HEADERS, timeout=10)
        claims = r.json().get('entities',{}).get(wid,{}).get('claims',{})
        claim = claims.get('P345',[])
        if claim:
            return claim[0]['mainsnak']['datavalue']['value']
    except:
        pass
    return None

def main():
    data, prefix, suffix = load_data_js()
    movies = [(i, m) for i, m in enumerate(data) if not (m.get('rating') or '').strip()]
    print(f'Movies without rating: {len(movies)}')

    results = []

    for idx, item in movies:
        title = item.get('title','')
        year = item.get('year','')
        stitle = clean_title(title)
        print(f'  {stitle} ({year})...', end=' ', flush=True)
        wid = search_wikipedia(stitle, year)
        if wid:
            imdb_id = get_imdb_from_wikidata(wid)
            if imdb_id and re.match(r'^tt\d+$', imdb_id):
                results.append({'index': idx, 'title': title, 'year': year, 'imdb_id': imdb_id})
                print(f'imdb={imdb_id}')
                time.sleep(0.3)
                continue
        print('-')
        time.sleep(0.3)

    # Save results
    output_path = os.path.join(SCRIPT_DIR, 'pending_ratings.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nSaved {len(results)} pending ratings to pending_ratings.json')

if __name__ == '__main__':
    main()
