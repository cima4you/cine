import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'رويال\data\results_royal.json', encoding='utf-8') as f:
    d = json.load(f)
for s in d:
    name = s.get('seriesName', '?')
    eps = s.get('episodes', [])
    nums = [e['number'] for e in eps]
    sorted_ok = nums == sorted(nums)
    print(f'{name[:45]}: {len(eps)} eps, numbers={nums}, sorted={sorted_ok}')
    for e in eps:
        print(f'  #{e["number"]}: {e["title"][:50]}')
