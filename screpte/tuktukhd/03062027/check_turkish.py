import json
with open('data.js','r',encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])
turkish = [(i,x) for i,x in enumerate(d) if x.get('type') == 'تركي']
print('Turkish in data.js:', len(turkish))
if turkish:
    for idx, item in turkish[:5]:
        print(f'  idx={idx}: "{item.get("title","").strip()[:50]}" ({item.get("year","")}) - poster tuktukhd: {item.get("poster","").startswith("https://tuktukhd")}')
    multi = sum(1 for _,x in turkish if any('متعدد' in s.get('name','') or 'جودة' in s.get('name','') for s in (x.get('servers') or [])))
    print(f'Multi-quality servers: {multi}')
