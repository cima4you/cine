import re, json, sys
sys.stdout.reconfigure(encoding="utf-8")

with open("data.js","r",encoding="utf-8") as f:
    text = f.read()

match = re.search(r"contentData\s*=\s*(\[.*?\])\s*;?\s*$", text, re.DOTALL)
data = json.loads(match.group(1))

from collections import Counter

# Check poster domains
domains = Counter()
poster_counts = Counter()
for item in data:
    p = item.get("poster","") or ""
    if p:
        # Extract domain
        m = re.search(r'https?://([^/]+)', p)
        if m:
            domains[m.group(1)] += 1
        poster_counts[p] += 1

print("Poster domains:")
for d,c in domains.most_common():
    print(f"  {d}: {c}")

# Check items where the type might be wrong
# Specifically check "انمي" vs "أنمي" - different Unicode Alef
anime1 = [i for i in data if i.get("type")=="انمي"]
anime2 = [i for i in data if i.get("type")=="أنمي"]
print(f"\nانمي items: {len(anime1)}")
print(f"أنمي items: {len(anime2)}")

# Check: are there items where contentType='series' but type suggests movie?
for item in data:
    if item.get("contentType")=="series":
        t = item.get("type","")
        if t in ("أجنبي", "هندي", "أسيوي"):
            pass  # Series can have these types too

# Check the "رمضان 2025" type - 22 items
ramadan = [i for i in data if i.get("type")=="رمضان 2025"]
print(f"\nرمضان 2025 items: {len(ramadan)}")
for r in ramadan[:5]:
    print(f"  {r.get('title','')[:40]} | poster: {str(r.get('poster',''))[:50]}")

# Check what "اخرى" type means
ukhra = [i for i in data if i.get("type")=="اخرى"]
print(f"\nاخرى items: {len(ukhra)}")
for u in ukhra:
    print(f"  {u.get('title','')[:40]} | {u.get('contentType','')}")

# Check any items where the poster is literally empty or the tmdb/omdb replacement failed
no_poster = [i for i in data if not i.get("poster")]
print(f"\nItems with no poster: {len(no_poster)}")
for n in no_poster[:10]:
    print(f"  {n.get('title','')[:50]} | type: {n.get('type','')} | ct: {n.get('contentType','')}")

# Check all type values for series items
series_types = Counter(i.get("type","") for i in data if i.get("contentType")=="series")
print(f"\nSeries by type:")
for t,c in series_types.most_common():
    print(f"  {repr(t)}: {c}")
