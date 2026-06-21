import re, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

def count_servers_in_file(path):
    print(f"=== {os.path.basename(path)} ===")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract JSON array
    m = re.search(r'\[\s*\{', content, re.DOTALL)
    if not m:
        print("  No array found")
        return
    start = m.start()
    # Find matching end
    depth = 0
    end = len(content)
    for i in range(start, len(content)):
        ch = content[i]
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    
    try:
        items = json.loads(content[start:end])
    except json.JSONDecodeError as e:
        print(f"  JSON error: {e}")
        return
    
    print(f"  Total series: {len(items)}")
    
    # Count series with servers
    with_servers = 0
    server_eps = 0
    total_eps = 0
    
    for item in items:
        has_servers = False
        for s in item.get('seasons', []):
            for e in s.get('episodes', []):
                total_eps += 1
                if e.get('servers'):
                    server_eps += 1
                    has_servers = True
        if has_servers:
            with_servers += 1
    
    print(f"  Series with servers: {with_servers}")
    print(f"  Total episodes: {total_eps}")
    print(f"  Episodes with servers: {server_eps}")
    
    # Sample first series with servers
    for item in items:
        for s in item.get('seasons', []):
            for e in s.get('episodes', []):
                sv = e.get('servers', [])
                if sv:
                    print(f"  Sample: {item['title'][:30]}...")
                    print(f"    Servers: {json.dumps(sv[:2], ensure_ascii=False)}")
                    print(f"    Format: {type(sv).__name__}")
                    if isinstance(sv, dict):
                        print(f"    Dict keys: {list(sv.keys())}")
                    elif isinstance(sv, list) and sv:
                        print(f"    List item keys: {list(sv[0].keys()) if isinstance(sv[0], dict) else type(sv[0])}")
                    return
    
    print("  NO series have servers!")

base = r'D:\web-secriping\Ancien PC\DT\site-rachid\data'
count_servers_in_file(os.path.join(base, 'data-turkish-completed.js'))
print()
count_servers_in_file(os.path.join(base, 'data-turkish-ongoing.js'))
