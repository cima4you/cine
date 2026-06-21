import json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check the full JSON for season values
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count how many series have null/missing season numbers
null_season = 0
multi_season = 0
season_nums = {}
for item in data:
    seasons = item.get('seasons', [])
    if len(seasons) > 1:
        multi_season += 1
    for s in seasons:
        sn = s.get('season')
        if sn is None:
            null_season += 1
        season_nums[str(sn)] = season_nums.get(str(sn), 0) + 1

print(f"Multi-season series: {multi_season}")
print(f"Seasons with null season number: {null_season}")
print(f"Season numbers distribution: {dict(sorted(season_nums.items()))}")

# Show example series with null seasons
for item in data:
    seasons = item.get('seasons', [])
    for s in seasons:
        if s.get('season') is None:
            print(f"\nExample: {item['title'][:40]}")
            print(f"  Seasons count: {len(seasons)}")
            for i, s2 in enumerate(seasons):
                print(f"  Season {i}: season={s2.get('season')}, eps={len(s2.get('episodes', []))}")
            break
    else:
        continue
    break
