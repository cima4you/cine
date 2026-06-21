import re, json, sys, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")

with open("data.js","r",encoding="utf-8") as f:
    text = f.read()

match = re.search(r"contentData\s*=\s*(\[.*?\])\s*;?\s*$", text, re.DOTALL)
data = json.loads(match.group(1))

# Check: for items with tmdb poster, does the poster match the title?
# TMDB posters are just paths, hard to verify. But let's check if any
# items have posters that obviously don't match.

# Check specific Arab series - see if their elcinema poster seems right
# by looking at the title and poster relationship
import hashlib

# Check if multiple series share the same poster
from collections import Counter
poster_titles = {}
for item in data:
    p = item.get("poster","")
    t = item.get("title","")
    if p and t:
        if p not in poster_titles:
            poster_titles[p] = []
        poster_titles[p].append(t)

# Find posters shared by multiple DIFFERENT titles
shared_posters = {p: titles for p, titles in poster_titles.items() if len(titles) > 1}
print(f"Posters shared by multiple items: {len(shared_posters)}")
for p, titles in list(shared_posters.items())[:20]:
    print(f"\n  Poster: {p[:60]}")
    for t in titles:
        print(f"    - {t[:50]}")

# Check for items that have a poster that doesn't match their type category
# e.g., Arabic type but English-looking title
print("\n\nPotential type mismatches (Arabic type but English title):")
arabic = [i for i in data if i.get("type")=="عربي"]
for a in arabic:
    t = a.get("title","")
    # If title has no Arabic characters at all
    if not re.search(r'[\u0600-\u06FF]', t):
        print(f"  {t[:50]} | poster: {str(a.get('poster',''))[:50]}")

print("\nPotential type mismatches (English type but Arabic title):")
foreign = [i for i in data if i.get("type")=="أجنبي"]
count = 0
for f in foreign:
    t = f.get("title","")
    # If title is mostly Arabic
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', t))
    total_chars = len(t.strip())
    if total_chars > 0 and arabic_chars / total_chars > 0.5:
        if count < 10:
            print(f"  {t[:50]} | poster: {str(f.get('poster',''))[:50]}")
        count += 1
print(f"  Total Arabic-titled items marked as 'أجنبي': {count}")
