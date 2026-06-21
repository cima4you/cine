import json
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])
turkish = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي']
tuk = sum(1 for _, x in turkish if 'tuktukhd' in x.get('poster', ''))
multi = sum(1 for _, x in turkish if any('متعدد' in s.get('name','') or 'جودة' in s.get('name','') for s in (x.get('servers') or [])))
no_servers = sum(1 for _, x in turkish if not x.get('servers'))
print('Turkish in data.js: {}'.format(len(turkish)))
print('With tuktukhd poster: {}'.format(tuk))
print('Multi-quality servers: {}'.format(multi))
print('No servers: {}'.format(no_servers))
