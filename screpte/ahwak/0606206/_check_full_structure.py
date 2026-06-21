import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

item = data[0]
print("Top-level keys:", list(item.keys()))
print("Title:", item["title"])
flat_eps = item.get('episodes', [])
print("Flat episodes:", len(flat_eps))
if flat_eps:
    print("Flat ep keys:", list(flat_eps[0].keys()))
    print("Flat ep seasonNumber:", flat_eps[0].get("seasonNumber"))

seasons = item.get("seasons", [])
print("\nSeasons count:", len(seasons))
for s in seasons:
    print(f"  Season keys: {list(s.keys())}")
    print(f"  SeasonNumber: {s.get('seasonNumber')}")
    print(f"  Episodes inside season: {len(s.get('episodes', []))}")
    break
