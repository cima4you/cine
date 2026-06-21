import re, json, sys, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")

with open("data.js","r",encoding="utf-8") as f:
    text = f.read()

match = re.search(r"contentData\s*=\s*(\[.*?\])\s*;?\s*$", text, re.DOTALL)
data = json.loads(match.group(1))

from collections import Counter

# Find posters shared by clearly different movies
# Group by poster URL
poster_groups = {}
for idx, item in enumerate(data):
    p = item.get("poster","")
    t = item.get("title","")
    if p and t:
        if p not in poster_groups:
            poster_groups[p] = []
        poster_groups[p].append((idx, t.strip()))

# For each shared poster, check if titles are truly different (not just different formatting of same movie)
def normalize_title(t):
    """Remove extra spaces, leading/trailing whitespace"""
    t = re.sub(r'\s+', ' ', t).strip().lower()
    t = re.sub(r'^\d{4}$', '', t)  # Remove if just a year
    return t

problematic = []
for p, items in poster_groups.items():
    if len(items) < 2:
        continue
    titles = [normalize_title(it[1]) for it in items]
    # Check if titles are genuinely different
    # Remove duplicates
    unique_titles = list(set(titles))
    # Filter out empty strings and pure years
    unique_titles = [t for t in unique_titles if t and not re.match(r'^\d{4}$', t)]
    if len(unique_titles) < 2:
        continue
    # Check if one title is substring of another or very similar
    real_diffs = []
    for i, t1 in enumerate(unique_titles):
        for j, t2 in enumerate(unique_titles):
            if i >= j:
                continue
            # Check if they share significant words
            words1 = set(t1.split())
            words2 = set(t2.split())
            if len(words1) > 2 and len(words2) > 2:
                common = words1 & words2
                if len(common) >= min(len(words1), len(words2)) * 0.5:
                    continue  # Similar enough, probably same movie
            # Check if one contains the other
            if t1 in t2 or t2 in t1:
                continue
            real_diffs.append((t1, t2))
    if real_diffs:
        problematic.append((p, items, real_diffs))

print(f"Posters shared by GENUINELY DIFFERENT movies: {len(problematic)}")
for p, items, diffs in problematic[:30]:
    print(f"\n  Poster: {p[:60]}")
    for idx, t in items:
        print(f"    [{idx}] {t[:60]}")
    print(f"  -> {len(diffs)} mismatched pairs")

# Save problematic items info
print(f"\n\nTotal problematic poster groups: {len(problematic)}")
total_affected = sum(len(items) for _, items, _ in problematic)
print(f"Total affected items: {total_affected}")
