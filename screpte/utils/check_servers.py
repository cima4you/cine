import json, sys
sys.stdout.reconfigure(encoding="utf-8")
from collections import Counter

with open(r"D:\Users\DT01\Desktop\rachid-site\data.js","r",encoding="utf-8") as f:
    raw = f.read()
start = raw.find("[")
end = raw.rfind("]")
items = json.loads(raw[start:end+1])
foreign = [i for i in items if i.get("type") == "أجنبي"]

# isDefault
default_count = sum(1 for i in foreign if i.get("servers") and any(s.get("isDefault") for s in i["servers"]))
no_default = sum(1 for i in foreign if i.get("servers") and not any(s.get("isDefault") for s in i["servers"]))
print(f"Items with isDefault server: {default_count}")
print(f"Items without isDefault: {no_default}")

# Duplicate server names
dup_count = 0
for i in foreign:
    servers = i.get("servers",[])
    names = [s.get("name","") for s in servers]
    if len(names) != len(set(names)):
        dup_count += 1
        dups = [n for n,c in Counter(names).items() if c > 1]
        if dups:
            t = i.get("title","?")
            print(f"  Duplicate names in {t}: {dups}")
print(f"\nItems with duplicate server names: {dup_count}")

# Items without servers or without download servers
no_servers = [i for i in foreign if not i.get("servers")]
no_dl = [i for i in foreign if not i.get("downloadServers")]
print(f"\nItems with NO top-level servers: {len(no_servers)} (all are series with servers in seasons)")
print(f"Items with NO top-level downloadServers: {len(no_dl)}")

# Check series specifically (data is inside seasons)
series = [i for i in foreign if i.get("contentType") == "series"]
print(f"\n=== Series analysis ({len(series)} items) ===")
issues = []
for i in series:
    seasons = i.get("seasons",[])
    if not seasons:
        issues.append(f"{i.get('title','?')}: no seasons")
        continue
    eps = seasons[0].get("episodes",[])
    if not eps:
        issues.append(f"{i.get('title','?')}: no episodes in season 0")
        continue
    ep = eps[0]
    if not ep.get("servers"):
        issues.append(f"{i.get('title','?')}: no servers in episode 0")
    if not ep.get("downloadServers"):
        issues.append(f"{i.get('title','?')}: no downloadServers in episode 0")
if issues:
    for iss in issues:
        print(f"  ISSUE: {iss}")
else:
    print("  All series have proper servers/downloadServers inside seasons[0].episodes[0]")

# Download server summary
dl_names = Counter()
for i in foreign:
    for ds in i.get("downloadServers",[]):
        dl_names[ds.get("name","?")] += 1
print(f"\nDownload server providers:")
for n, c in dl_names.most_common(10):
    print(f"  {n}: {c}")
