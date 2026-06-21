import os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'D:\web-secriping\Ancien PC\DT\site-rachid'

for fname in ['data-turkish-completed.js', 'data-turkish-ongoing.js']:
    fpath = os.path.join(base, 'data', fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read(5000)
    
    print(f"=== {fname} (first 300 bytes) ===")
    print(content[:300])
    print()
    
    total_servers = content.count('servers')
    print(f"Total 'servers' occurrences: {total_servers}")
    
    # Show first servers block
    idx = content.find('servers')
    if idx > 0:
        print("First 'servers' context:")
        print(content[idx:idx+200])
    print()
