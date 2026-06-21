import json

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Remove ALL entries with type تركي
new_d = [item for item in d if item.get('type') != 'تركي']

removed = len(d) - len(new_d)
print('Removed {} Turkish entries'.format(removed))
print('Total before: {}, after: {}'.format(len(d), len(new_d)))

prefix = content[:content.index('[')]
suffix = content[content.rindex(']') + 1:]
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + json.dumps(new_d, ensure_ascii=False) + suffix)
print('Saved data.js')
