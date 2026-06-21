import re, json, sys
sys.stdout.reconfigure(encoding="utf-8")

with open("data.js","r",encoding="utf-8") as f:
    text = f.read()

match = re.search(r"contentData\s*=\s*(\[.*?\])\s*;?\s*$", text, re.DOTALL)
data = json.loads(match.group(1))

from collections import Counter
types = Counter(i.get("type","") for i in data)
print("Type field values:")
for t,c in types.most_common():
    print(f"  {repr(t)}: {c}")

# Check: contentType vs type overlap
ct_types = Counter(i.get("contentType","") for i in data)
print("\ncontentType values:")
for t,c in ct_types.most_common():
    print(f"  {repr(t)}: {c}")

# Check for items where the type means their poster might be wrong
# Check some specific series titles
print("\nSample series poster check:")
series = [i for i in data if i.get("contentType")=="series"]
for s in series[:10]:
    t = s.get("title","")[:50]
    p = s.get("poster","")[:60]
    print(f"  {t} -> {p}")

# Check if any poster URLs look like they belong to a different site/series
# Look for mismatched patterns
print("\nChecking for poster mismatches...")
# Look for items whose poster URL contains a title that doesn't match
for item in data[:2000]:
    poster = item.get("poster","") or ""
    title = item.get("title","") or ""
    if not poster or not title:
        continue
    # If poster URL has Arabic text, check if it matches title
    arabic_in_url = re.findall(r'[\u0600-\u06FF]+', poster)
    if arabic_in_url:
        url_arabic = " ".join(arabic_in_url)
        # If poster URL has Arabic but title doesn't match at all
        title_keywords = re.findall(r'[\u0600-\u06FF]+', title)
        if title_keywords and not any(k in url_arabic for k in title_keywords[:2]):
            print(f"  POSSIBLE MISMATCH: {title[:40]} | poster URL has: {url_arabic[:40]}")
