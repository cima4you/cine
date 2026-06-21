import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Find ALL duplicate seasons in both files
def find_duplicates(items, label):
    dup_count = 0
    seen_seasons = {}
    for item in items:
        seasons = item.get('seasons', [])
        for s in seasons:
            sn = s.get('season', None)
            # Also check seasonNumber
            if sn is None:
                sn = s.get('seasonNumber', None)
            if sn is None:
                sn = 0  # Default for identification
            key = (item.get('title', ''), sn)
            if key in seen_seasons:
                dup_count += 1
                print(f"{label}: {item['title'][:30]} — Season {sn} DUPLICATE")
            seen_seasons[key] = s
    return dup_count

# Check source
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_full.json', 'r', encoding='utf-8') as f:
    source = json.load(f)
print("=== Source (full.json) ===")
src_dups = find_duplicates(source, "Source")
print(f"Source duplicates: {src_dups}")

print()

# Check old formatted
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\ahwaktv_data_formatted.json', 'r', encoding='utf-8') as f:
    old = json.load(f)
print("=== Old (formatted.json) ===")
old_dups = find_duplicates(old, "Old")
print(f"Old duplicates: {old_dups}")
