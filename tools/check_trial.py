import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
arr_start = content.index('[')
arr_end = content.rindex(']') + 1
data = json.loads(content[arr_start:arr_end])

movies = [m for m in data if m.get('contentType') == 'movie']
with_trial = [m for m in movies if m.get('trial')]
print(f'Movies with trial: {len(with_trial)} out of {len(movies)}')

series = [m for m in data if m.get('contentType') == 'series']
s_with_trial = 0
for s in series:
    seasons = s.get('seasons', [])
    for season in seasons:
        if season.get('trial'):
            s_with_trial += 1
            break
print(f'Series with trial: {s_with_trial} out of {len(series)}')

# Show sample trial URLs
if with_trial:
    print('\nSample movie trial:')
    for m in with_trial[:3]:
        print(f'  {m["title"]}: {m["trial"][:80]}')
