import json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check detail JSON for season values
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_detail.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count how many have proper season info
has_seasons = 0
null_season = 0
for item in data:
    ss = item.get('seasons', [])
    if ss:
        has_seasons += 1
        for s in ss:
            sn = s.get('seasonNumber')
            if sn is None:
                null_season += 1

print(f"Series with seasons field: {has_seasons} / {len(data)}")
print(f"Season entries with null seasonNumber: {null_season}")

# Show example
for item in data:
    ss = item.get('seasons', [])
    if ss:
        print(f"\nExample: {item['title'][:40]}")
        for s in ss:
            print(f"  seasonNumber={s.get('seasonNumber')}, name={s.get('name', '')}")
        break
