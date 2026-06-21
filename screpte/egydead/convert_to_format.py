import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')

INPUT = r'D:\Users\DT01\Desktop\rachid-site\scripts\egydead\egydead.json'
OUTPUT = r'D:\Users\DT01\Desktop\rachid-site\scripts\egydead\egydead_formatted.json'

with open(INPUT, 'r', encoding='utf-8') as f:
    episodes = json.load(f)

def parse_season_ep(ep):
    """Extract season and episode number from URL and title"""
    url = ep['url'].rstrip('/')
    slug = url.split('/')[-1]
    title = ep.get('title', '')
    season = 1
    episode = 1
    
    # From URL: s01e85 or s01e85-ar
    m = re.search(r's(\d+)e(\d+)', slug, re.I)
    if m:
        season = int(m.group(1))
        episode = int(m.group(2))
    else:
        m = re.search(r'-e(\d+)', slug)
        if m:
            episode = int(m.group(1))
    
    # From title: الجزء X
    m = re.search(r'الجزء\s*(\w+)', title)
    if m:
        part_word = m.group(1)
        part_map = {'الاول': 1, 'الثاني': 2, 'الثالث': 3, 'الرابع': 4, 'الخامس': 5}
        if part_word in part_map:
            season = part_map[part_word]
        elif part_word.isdigit():
            season = int(part_word)
    
    # From title: الحلقة Y
    m = re.search(r'الحلقة\s*(\d+)', title)
    if m:
        episode = int(m.group(1))
    
    # From title: الموسم Z
    m = re.search(r'الموسم\s*(\w+)', title)
    if m:
        part_word = m.group(1)
        part_map = {'الاول': 1, 'الثاني': 2, 'الثالث': 3, 'الرابع': 4, 'الخامس': 5}
        if part_word in part_map:
            season = part_map[part_word]
        elif part_word.isdigit():
            season = int(part_word)
    
    return season, episode

def extract_year(ep):
    """Extract year from description or title"""
    desc = ep.get('description', '')
    title = ep.get('title', '')
    text = desc + ' ' + title
    years = re.findall(r'\b(20\d{2})\b', text)
    for y in years:
        yi = int(y)
        if 2020 <= yi <= 2030:
            return y
    return ''

def extract_poster(ep):
    """Get best poster URL"""
    cover = ep.get('cover', '')
    image = ep.get('image', '')
    return cover or image  # cover is full size, image is thumbnail

def clean_series_name(name):
    """Clean series name"""
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def get_original_name(ep):
    """Extract original (non-Arabic) name from description"""
    desc = ep.get('description', '')
    # Arabic stream sites often have: Arabic name + original name in the description
    # Look for English/Turkish names
    # This is tricky, return empty for now
    return ''

def get_quality(ep):
    """Infer quality from label or description"""
    label = ep.get('label', '')
    desc = ep.get('description', '')
    if '1080' in desc or 'HD' in desc.upper():
        return 'HD'
    return 'متعدد'

# ============ Process ============
seen_episodes = set()
series_map = {}  # series_name -> list of episodes (grouped for merging)

for ep in episodes:
    name = clean_series_name(ep['series_name'])
    
    # Determine base series name (without الجزء X suffix for grouping)
    base_name = re.sub(r'\s+الجزء\s+\w+$', '', name)
    base_name = re.sub(r'\s+الموسم\s+\w+$', '', base_name)
    # Also handle "2024 مترجم و" suffix
    base_name = re.sub(r'\s+\d{4}\s+مترجم\s+و\s*$', '', base_name)
    
    if base_name not in series_map:
        series_map[base_name] = []
    series_map[base_name].append(ep)

# Deduplicate episodes by URL
for base_name in series_map:
    seen = set()
    unique = []
    for ep in series_map[base_name]:
        if ep['url'] not in seen:
            seen.add(ep['url'])
            unique.append(ep)
    series_map[base_name] = unique

# Build formatted output
output = []
for base_name, eps in sorted(series_map.items()):
    # Use first episode with description for series-level info
    first_with_desc = next((e for e in eps if e.get('description')), eps[0])
    
    # Parse year
    year = extract_year(first_with_desc)
    
    # Group into seasons
    seasons_dict = {}
    for ep in eps:
        season_num, episode_num = parse_season_ep(ep)
        if season_num not in seasons_dict:
            seasons_dict[season_num] = []
        
        # Create episode entry
        ep_entry = {
            'episodeNumber': episode_num,
            'title': ep.get('title', ''),
            'duration': '',
            'servers': [],
            'downloadServers': []
        }
        
        # Add servers (first one as default)
        sv = ep.get('servers', [])
        for i, s in enumerate(sv):
            ep_entry['servers'].append({
                'name': f'server{i+1}',
                'url': s.get('url', ''),
                'isDefault': i == 0
            })
        
        seasons_dict[season_num].append(ep_entry)
    
    # Sort episodes within each season
    for sn in seasons_dict:
        seasons_dict[sn].sort(key=lambda x: x['episodeNumber'])
    
    # Create series entry
    series_entry = {
        'title': base_name,
        'originalName': get_original_name(first_with_desc),
        'year': year,
        'rating': '',
        'type': 'تركي',
        'contentType': 'series',
        'description': (first_with_desc.get('description') or '')[:500],
        'cast': [],
        'poster': extract_poster(first_with_desc),
        'categories': ['مسلسلات تركية'],
        'quality': get_quality(first_with_desc),
        'seasons': []
    }
    
    # Add seasons in order
    for sn in sorted(seasons_dict.keys()):
        series_entry['seasons'].append({
            'seasonNumber': sn,
            'trial': '',
            'description': '',
            'poster': '',
            'episodes': seasons_dict[sn]
        })
    
    output.append(series_entry)

# Save
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'Converted {len(episodes)} episodes → {len(output)} series')
print(f'Output: {OUTPUT}')

# Stats
total_seasons = sum(len(s['seasons']) for s in output)
total_eps_in_output = sum(len(se['episodes']) for s in output for se in s['seasons'])
total_servers = sum(len(ep['servers']) for s in output for se in s['seasons'] for ep in se['episodes'])
print(f'Total seasons: {total_seasons}')
print(f'Total episodes (formatted): {total_eps_in_output}')
print(f'Total server links: {total_servers}')

# Show series list
print(f'\nSeries ({len(output)}):')
for s in output:
    eps_count = sum(len(se['episodes']) for se in s['seasons'])
    seasons_count = len(s['seasons'])
    print(f'  {s["title"]} ({s["year"]}) - {seasons_count} seasons, {eps_count} episodes')
