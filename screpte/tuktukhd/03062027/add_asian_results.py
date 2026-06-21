import json, re

with open('scripts/tuktukhd/data/results_asian.json', 'r', encoding='utf-8') as f:
    new_items = json.load(f)

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

def clean_title(raw):
    t = re.sub(r'فيلم|فلم|مسلسل|مترجم|اون\s*لاين|أون\s*لاين|اون-لاين|عربي|مدبلج', '', raw, flags=re.IGNORECASE).strip()
    t = re.sub(r'[\u0600-\u06FF]+', '', t).strip()
    t = re.sub(r'\s{2,}', ' ', t).strip()
    t = re.sub(r'^[\s\-,;:.]+|[\s\-,;:.]+$', '', t).strip()
    return t if t else raw

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

# Check format
sample = new_items[0] if new_items else {}
has_titre = 'titre' in sample
has_title = 'title' in sample

existing = set()
for item in data_js:
    existing.add((norm(item.get('title', '')), str(item.get('year', ''))))

added = 0
skipped = 0
for item in new_items:
    # Convert from foreign format (titre, image, video_url, servers, info) to data.js format
    if has_titre:
        title = clean_title(item.get('titre', ''))
        year = item.get('info', {}).get('details', {}).get('موعد الصدور :', item.get('year', ''))
        poster = item.get('image', '')
        desc = item.get('info', {}).get('story', '')
        categories = item.get('info', {}).get('catssection', [])
        details = item.get('info', {}).get('details', {})
        duration = details.get('توقيت الفيلم :', '')
        quality = details.get('جودة الفيلم :', '')
        cast_raw = details.get('بطولة :', '')
        cast = [a.strip() for a in re.split(r'[-–—,/\n]+', cast_raw) if a.strip()] if cast_raw else []

        servers_raw = item.get('servers', {}).get('watch', [])
        servers = []
        for s in servers_raw:
            servers.append({
                "name": s.get('name', 'Server'),
                "url": s.get('url', ''),
                "isDefault": s.get('isDefault', False)
            })
        download_raw = item.get('servers', {}).get('download', [])
        download_servers = []
        for s in download_raw:
            download_servers.append({
                "name": s.get('name', 'Download'),
                "url": s.get('url', '')
            })
        
        entry = {
            'title': title,
            'year': year,
            'type': 'أسيوي',
            'servers': servers,
            'downloadServers': download_servers,
            'trial': '',
            'contentType': 'movie',
        }
        if poster: entry['poster'] = poster
        if desc: entry['description'] = desc
        if duration: entry['duration'] = duration
        if quality: entry['quality'] = quality
        if cast: entry['cast'] = cast
        if categories: entry['categories'] = categories
    else:
        # Already in data.js format
        entry = item
        title = item.get('title', '')
        year = item.get('year', '')
        entry['trial'] = ''
        entry['contentType'] = 'movie'
    
    if not title or not year:
        skipped += 1
        continue
    
    key = (norm(title), str(year))
    if key in existing:
        skipped += 1
        continue
    
    data_js.append(entry)
    existing.add(key)
    added += 1

if added > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    json_str = json.dumps(data_js, ensure_ascii=False)
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)

print('Added: {} | Skipped: {} | Total: {}'.format(added, skipped, len(data_js)))
