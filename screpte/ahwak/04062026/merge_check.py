import sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Count total episodes in ahwaktv data
with open('scripts/ahwak/ahwaktv_data_formatted.json', 'r', encoding='utf-8') as f:
    ahwa = json.load(f)
total_eps = sum(len(s['seasons'][0]['episodes']) for s in ahwa if s.get('seasons'))
print(f'Ahwaktv: {len(ahwa)} series, {total_eps} total episodes')

# Check existing Turkish series in data.js
content = open('data.js', 'r', encoding='utf-8').read()
json_str = content.split('const contentData = ')[1].rsplit(';', 1)[0]
data = json.loads(json_str)
turkish_series = [s for s in data if s.get('type') in ('تركي','تركيي') and s.get('contentType') == 'series']
print(f'Existing Turkish series in data.js: {len(turkish_series)}')

# Show one example
if turkish_series:
    s = turkish_series[0]
    print(f'\nExample Turkish series entry:')
    print(f'  title: {s.get("title","")[:60]}')
    print(f'  servers: {len(s.get("servers",[]))} entries')
    print(f'  downloadServers: {len(s.get("downloadServers",[]))} entries')
    print(f'  Keys: {list(s.keys())}')
