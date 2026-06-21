import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open("data/turkish_series_full.json", encoding="utf-8") as f:
    data = json.load(f)

s = data[0]
print("title:", s.get("title"))
eps = s.get("episodes", [])
print("episodes count:", len(eps))
if eps:
    e = eps[0]
    servers = e.get("servers", [])
    print("servers count:", len(servers))
    print("server type:", type(servers).__name__)
    print("sample:", json.dumps(servers[:3], ensure_ascii=False))
