import json, re

path = r"D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-completed.js"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
m = re.search(r"const cd_turkish_completed = (\[)", content)
start = m.start(1)
depth = 0
for i in range(start, len(content)):
    if content[i] == "[": depth += 1
    elif content[i] == "]":
        depth -= 1
        if depth == 0:
            items = json.loads(content[start:i+1])
            break

for item in items:
    title = item.get("title", "")
    for s in item.get("seasons", []):
        for e in s.get("episodes", []):
            sv = e.get("servers", [])
            epnum = e.get("episodeNumber", "")
            if not sv:
                print(f"EMPTY: {title} ep {epnum}")
            elif isinstance(sv, list) and len(sv) > 0 and isinstance(sv[0], dict) and sv[0].get("name") == "watch":
                print(f"WATCH: {title} ep {epnum} url={sv[0].get('url','')[:60]}")
