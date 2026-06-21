import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

def check_file(path, label):
    print(f"=== {label} ===")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    m = re.search(r'\[\s*\{', content, re.DOTALL)
    start = m.start()
    depth = 0
    for i in range(start, len(content)):
        if content[i] == '[': depth += 1
        elif content[i] == ']':
            depth -= 1
            if depth == 0:
                items = json.loads(content[start:i+1])
                break
    
    # Count episodes and servers
    total_eps = 0
    total_series = len(items)
    eps_with_servers = 0
    series_with_servers = 0
    
    for item in items:
        has_sv = False
        for s in item.get('seasons', []):
            for ep in s.get('episodes', []):
                total_eps += 1
                if ep.get('servers'):
                    eps_with_servers += 1
                    has_sv = True
        if has_sv:
            series_with_servers += 1
    
    print(f"  Series: {total_series}")
    print(f"  Episodes: {total_eps}")
    print(f"  Eps with servers: {eps_with_servers}")
    print(f"  Series with servers: {series_with_servers}")
    
    # Check no duplicates
    dup_count = 0
    for item in items:
        seasons = item.get('seasons', [])
        seen = set()
        for s in seasons:
            sn = s.get('seasonNumber', s.get('season', None))
            if sn in seen:
                dup_count += 1
            seen.add(sn)
    
    print(f"  Duplicate seasons: {dup_count}")
    print()

check_file(r'D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-completed.js', 'المكتملة')
check_file(r'D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-ongoing.js', 'المستمرة')
