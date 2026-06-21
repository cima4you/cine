import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = json.load(open(r'رويال\data\results_royal.json', encoding='utf-8'))
print(f'Series: {len(data)}')
for s in data:
    eps = s.get('episodes', [])
    total_srv = sum(len(ep.get('servers', [])) for ep in eps)
    print(f'\n--- {s.get("seriesName","")} ---')
    print(f'  Title: {s.get("title","")}')
    print(f'  Description: {(s.get("description","") or "")[:100]}')
    print(f'  Episodes: {len(eps)}')
    print(f'  Servers total: {total_srv}')
    if eps:
        e = eps[0]
        print(f'  First ep #{e["number"]}: {len(e.get("servers",[]))} servers')
        if e.get('servers'):
            print(f'  Sample server: {e["servers"][0]}')
    print(f'  Keys: {list(s.keys())}')
