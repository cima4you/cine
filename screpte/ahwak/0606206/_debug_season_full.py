import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

item = data[0]
print("Title:", item["title"])
print("Seasons count:", len(item.get("seasons", [])))
for s in item.get("seasons", []):
    print("  Season dict keys:", list(s.keys()))
    print("  season value:", s.get("season"))
    print("  Is None?", s.get("season") is None)
    print("  Type:", type(s.get("season")))
    # Check if key exists
    print("  season key exists?", "season" in s)
    if s.get("episodes"):
        ep = s["episodes"][0]
        print("  Episode keys:", list(ep.keys()))
        print("  seasonNumber:", ep.get("seasonNumber"))
    break
