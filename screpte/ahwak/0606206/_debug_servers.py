import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

# Use absolute path based on script location
base = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base, "data", "turkish_series_full.json")

print("json_path:", json_path)
print("exists:", os.path.exists(json_path))

with open(json_path, encoding="utf-8") as f:
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
