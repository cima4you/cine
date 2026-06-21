import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = json.load(open(r'رويال\data\results_listing.json', encoding='utf-8'))
print(f'Total: {len(data)}')
for i, it in enumerate(data):
    print(f'{i+1}. title: {it["title"][:60]}')
    print(f'   series: {it["seriesName"][:40]} | ep: {it["episodeNumber"]} | vid: {it["vid"]}')
