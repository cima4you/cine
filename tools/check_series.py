import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
arr_start = content.index('[')
arr_end = content.rindex(']') + 1
data = json.loads(content[arr_start:arr_end])

series = [m for m in data if m.get('contentType') == 'series']
movies = [m for m in data if m.get('contentType') == 'movie']
print(f'Series: {len(series)}, Movies: {len(movies)}')
print()

for s in series[:5]:
    t = s.get('title', '?')
    sv = len(s.get('servers', []))
    dv = len(s.get('downloadServers', []))
    tr = s.get('trial', '')[:50]
    print(f'  {t} | servers={sv} download={dv} trial={bool(tr)}')
    if sv == 0 and not tr:
        print(f'    NO WATCH OPTIONS!')
        print(f'    servers field:', s.get('servers', 'MISSING'))
        print(f'    keys:', list(s.keys()))
    print()

# Check how many series have no viewing options
no_watch = [s for s in series if not s.get('servers') and not s.get('trial')]
print(f'Series without any watch option: {len(no_watch)}')
no_download = [s for s in series if not s.get('downloadServers')]
print(f'Series without download: {len(no_download)}')

# Sample a series with no servers
if no_watch:
    print('\nSample no-watch series:')
    s = no_watch[0]
    print(json.dumps(s, ensure_ascii=False, indent=2)[:500])
