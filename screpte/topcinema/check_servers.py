import json
with open('D:\\Users\\DT01\\Desktop\\rachid-site\\scripts\\topcinema\\data\\topcinema_detail.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for m in data:
    sv = m.get('servers', [])
    if sv:
        print('Movie: {}'.format(m['title']))
        print('  Servers: {}'.format(len(sv)))
        for s in sv:
            n = s['name'].encode('unicode-escape').decode('ascii')
            u = s['url'].encode('unicode-escape').decode('ascii') if s['url'] else '(empty)'
            print('    {}: {}'.format(n, u[:80]))
        break
