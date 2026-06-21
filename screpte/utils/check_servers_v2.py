import json
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data = json.loads(content[start:end])
all_names = set()
for item in data:
    for s in item.get('servers', []):
        all_names.add(s.get('name', ''))
print('All unique server names ({}):'.format(len(all_names)))
for n in sorted(all_names):
    print('  "{}"'.format(n))
