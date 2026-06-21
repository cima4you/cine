import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'رويال\data\results_royal.json', encoding='utf-8') as f:
    d = json.load(f)
print('Series:', len(d))
for s in d:
    name = s.get('seriesName', '?')
    eps = s.get('episodes', [])
    print(f'  {name[:40]}: {len(eps)} episodes')
    nums = [e['number'] for e in eps]
    sorted_ok = nums == sorted(nums)
    print(f'    numbers: {nums[:5]}... sorted={sorted_ok}')
