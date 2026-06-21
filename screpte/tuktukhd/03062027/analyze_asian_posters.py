import json, re, requests, concurrent.futures

headers = {'User-Agent': 'Mozilla/5.0'}

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

asian = [x for x in d if x.get('type') == 'أسيوي']
print('Total Asian movies in data.js: {}'.format(len(asian)))

# Load tuktukhd Asian index
try:
    with open('scripts/tuktukhd/data/tuktuk_asian_index.json', 'r', encoding='utf-8') as f:
        asian_index = json.load(f)
    print('Tuktukhd Asian index: {}'.format(len(asian_index)))
except:
    asian_index = []
    print('No tuktukhd Asian index found')

# Also load sitemap for wider matching
try:
    with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
        sitemap = json.load(f)
    print('Sitemap index: {}'.format(len(sitemap)))
except:
    sitemap = []
    print('No sitemap index found')

# Build normalized lookup from tuktukhd data
def super_norm(t):
    t = t.lower().strip()
    t = re.sub(r'\s+\d{4}$', '', t)
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    t = re.sub(r'\s+', '', t.replace('ü','u').replace('ğ','g').replace('ş','s').replace('ı','i').replace('ö','o').replace('ç','c'))
    return t.strip()

from difflib import SequenceMatcher

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

# Check poster coverage
with_poster = sum(1 for x in asian if x.get('poster', ''))
without_poster = sum(1 for x in asian if not x.get('poster', ''))
print('\nWith poster: {}, Without poster: {}'.format(with_poster, without_poster))

# Try to match against tuktukhd indexes
combined_index = (asian_index or []) + (sitemap or [])
existing_norm = {(norm(x['name']), x['year']): x for x in combined_index}

matchable = 0
unmatchable = 0
for item in asian:
    title = item.get('title', '').strip()
    year = str(item.get('year', ''))
    key = (norm(title), year)
    if key in existing_norm:
        matchable += 1
    else:
        # Try fuzzy
        tn = super_norm(title)
        found = False
        for x in combined_index:
            if x['year'] == year:
                xn = super_norm(x['name'])
                if tn == xn or (len(tn) >= 5 and len(xn) >= 5 and (tn in xn or xn in tn)):
                    found = True
                    break
        if found:
            matchable += 1
        else:
            unmatchable += 1

print('Matchable to tuktukhd: {}'.format(matchable))
print('Unmatchable: {}'.format(unmatchable))

# Sample some posters
print('\nSample posters from Asian movies:')
for item in asian[:5]:
    print('  "{}" ({}) -> poster: {}'.format(
        item.get('title','').strip(), item.get('year',''),
        item.get('poster','(none)')[:80]))
