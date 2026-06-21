import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = json.load(open('results_animerco_animes.json', encoding='utf-8'))
print('=== Series with 1 season / 1 episode (possibly movies) ===')
for a in d:
    seasons = a.get('seasons', [])
    if len(seasons) == 1:
        eps = seasons[0].get('episodes', [])
        if len(eps) == 1:
            title = a.get('title', '')
            year = a.get('year', '')
            print(f'  {title[:50]} ({year}) - 1 season, 1 episode')
