import json
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
d = json.loads(c[c.index('['):c.rindex(']')+1])
target = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
          'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']
rem = [(x.get('title','').strip(), x.get('year',''), x.get('type',''))
       for x in d if any(s.get('name','') in target for s in x.get('servers',[]))]
print('Items with multi-quality: {}'.format(len(rem)))
for t,y,ty in rem:
    print('  "{}" ({}) [{}]'.format(t,y,ty))
