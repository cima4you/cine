import json
m = json.load(open('screpte/cimafre/data/cimafre_movies.json', 'r', encoding='utf-8'))
print(f'Total: {len(m)}')
for x in m[:5]:
    embed = x.get('embed_url', 'NONE')
    print(f'{x["vid"]}: {x.get("title","?")[:50]} | embed: {embed[:70] if embed != "NONE" else "NONE"}')
