import os, re, json
from collections import Counter

data_dir = 'data'
for fname in os.listdir(data_dir):
    if fname.startswith('data-turkish') and fname.endswith('.js'):
        fpath = os.path.join(data_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        m = re.search(r'=\s*(\\[.*?\\]);', content, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                titles = [d.get('title','') for d in data]
                counts = Counter(titles)
                dupes = {k:v for k,v in counts.items() if v > 1}
                print(f'{fname}: {len(data)} items, {len(dupes)} dupes')
                if dupes:
                    for t,c in sorted(dupes.items(), key=lambda x:-x[1])[:10]:
                        print(f'  "{t}" x{c}')
            except Exception as e:
                print(f'{fname}: {e}')
