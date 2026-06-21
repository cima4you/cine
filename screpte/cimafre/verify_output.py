import json
m = json.load(open('data/data-cimafre.json', 'r', encoding='utf-8'))
print(f'Total: {len(m)} movies')
for movie in m[:2]:
    print(f'\n{movie["title"][:60]}')
    print(f'  Servers: {len(movie.get("servers", []))}')
    for s in movie.get('servers', [])[:3]:
        print(f'    [{s["id"]}] {s["name"]}: {s["url"][:70]}')
    if movie.get('downloads'):
        print(f'  Downloads: {len(movie["downloads"])}')
        for d in movie['downloads'][:2]:
            print(f'    {d["name"]}: {d["url"][:70]}')
