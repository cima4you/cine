import json, re, base64, urllib.parse

DATA_FILE = r"data\data-foreign.js"

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r"\[", content)
start = m.start()
depth = 0
for i in range(start, len(content)):
    if content[i] == "[": depth += 1
    elif content[i] == "]":
        depth -= 1
        if depth == 0:
            items = json.loads(content[start:i+1])
            break

prefix = content[:start]
suffix = content[i+1:]
var_match = re.search(r'(const|let|var)\s+(\w+)\s*=', prefix)
var_name = var_match.group(2) if var_match else 'movies'

fixed = 0
for item in items:
    ds = item.get('downloadServers', [])
    for d in ds:
        url = d.get('url', '')
        if 'go.php' in url:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'u' in qs:
                try:
                    decoded = base64.b64decode(qs['u'][0]).decode('utf-8')
                    if decoded and decoded != url:
                        d['url'] = decoded
                        fixed += 1
                except:
                    pass

lbl = re.search(r'— \d+ عنصر', prefix)
count_label = f'// أفلام أجنبية — {len(items)} عنصر\n'
prefix = re.sub(r'//.*?عنصر', count_label.strip(), prefix)

with open(DATA_FILE, 'w', encoding='utf-8') as f:
    f.write(f'// أفلام أجنبية — {len(items)} عنصر\n')
    f.write(f'// تم فك تشفير: {fixed} رابط تحميل\n')
    f.write(f'const {var_name} = ')
    json.dump(items, f, ensure_ascii=False)

print(f'فُك {fixed} رابط تحميل من أصل {len(items)} فيلم')
