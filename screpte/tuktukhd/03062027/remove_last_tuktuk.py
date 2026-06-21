import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(SCRIPT_DIR, 'data.js')

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

prefix = content[:content.index('[')]
suffix = content[content.rindex(']')+1:]
data = json.loads(content[content.index('['):content.rindex(']')+1])

def is_tuktuk(m):
    for s in m.get('servers', []):
        url = s.get('url', '')
        if 'tuktukhd.com/watch?token' in url or 'megatuktuk.store' in url:
            return True
    return False

tuktuk_indices = [i for i, m in enumerate(data) if is_tuktuk(m)]
print(f'Total: {len(data)}, Tuktuk items: {len(tuktuk_indices)}')

to_remove = set(tuktuk_indices[-2:])
print(f'Removing last {len(to_remove)} tuktuk items (indices {min(to_remove)}-{max(to_remove)})')

new_data = [m for i, m in enumerate(data) if i not in to_remove]
removed = len(data) - len(new_data)

json_str = json.dumps(new_data, ensure_ascii=False)
with open(path, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)

size = os.path.getsize(path)
print(f'Removed: {removed} | Remaining: {len(new_data)} | Size: {size/1024:.0f} KB')
