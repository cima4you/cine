import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('screpte\\tuktukhd\\tuktuk\\افلام.json', encoding='utf-8') as f:
    data = json.load(f)
for i, m in enumerate(data, 1):
    print(f'{i:2d}. {m["title"]}')
