import json, re, sys, urllib.request

path = r"D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-completed.js"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
m = re.search(r"const \w+ = (\[)", content)
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
    for s in item.get("seasons", []):
        for e in s.get("episodes", []):
            sv = e.get("servers", [])
            if sv and isinstance(sv, list) and sv[0].get("name") == "watch":
                title = item.get("title")
                etitle = e.get("title")
                vid_url = sv[0]["url"]
                print(f"Item: {title}")
                print(f"Ep: {etitle}")
                print(f"URL: {vid_url}")
                m2 = re.search(r"[?&]vid=([0-9a-fA-F]+)", vid_url)
                vid = m2.group(1) if m2 else "N/A"
                print(f"Vid: {vid}")
                see_url = f"https://yam.ahwaktv.net/see.php?vid={vid}"
                HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                try:
                    req = urllib.request.Request(see_url, headers=HEADERS)
                    resp = urllib.request.urlopen(req, timeout=20)
                    html = resp.read().decode("utf-8", errors="replace")
                    print(f"Response: {len(html)} bytes, data-embed-url: {'data-embed-url' in html}")
                    for mm in re.finditer(r'data-embed-url="([^"]+)"', html):
                        print(f"  embed: {mm.group(1)[:60]}")
                    if not re.search(r"data-embed-url", html):
                        print(f"HTML[0:300]: {html[:300]}")
                except Exception as ex:
                    print(f"Fetch error: {ex}")
                break
        else:
            continue
        break
    else:
        continue
    break
