import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('scripts/ahwak/data/results_yam_moslslat_ramadan_2024.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Total series: %d' % len(data))
total_eps = sum(len(s['seasons'][0]['episodes']) for s in data)
total_servers = sum(1 for s in data for ep in s['seasons'][0]['episodes'] for _ in ep['servers'])
print('Total episodes: %d' % total_eps)
print('Total servers: %d' % total_servers)

# Check poster breakdown
poster_types = {'yam': 0, 'elcinema': 0, 'other': 0, 'empty': 0}
for s in data:
    p = s.get('poster', '')
    if not p:
        poster_types['empty'] += 1
    elif 'elcinema' in p.lower():
        poster_types['elcinema'] += 1
    elif 'yam' in p.lower():
        poster_types['yam'] += 1
    else:
        poster_types['other'] += 1

print('\nPoster breakdown:', poster_types)

# Show first 5 series
print('\nFirst 5 series:')
for s in data[:5]:
    print('  %s | year=%s | eps=%d | posters=%s' % (
        s['title'][:40], s['year'],
        len(s['seasons'][0]['episodes']),
        s['poster'][:50] if s['poster'] else 'NONE'))
