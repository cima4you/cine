import json, re, urllib.request

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
                vid_url = sv[0]["url"]
                m2 = re.search(r"[?&]vid=([0-9a-fA-F]+)", vid_url)
                vid = m2.group(1) if m2 else None
                if not vid:
                    continue
                see_url = f"https://yam.ahwaktv.net/see.php?vid={vid}"
                HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                try:
                    req = urllib.request.Request(see_url, headers=HEADERS)
                    resp = urllib.request.urlopen(req, timeout=20)
                    html = resp.read().decode("utf-8", errors="replace")
                    # Search around data-embed-url to see actual HTML structure
                    idx = html.find("data-embed-url")
                    if idx >= 0:
                        print(f"Context around data-embed-url [{item.get('title')}]:")
                        print(html[max(0,idx-200):idx+400])
                        print("---")
                    else:
                        print(f"No data-embed-url found for {item.get('title')}")
                    # Also check extract_servers
                    servers = []
                    for mm in re.finditer(r'<li[^>]*data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
                        url = mm.group(1)
                        name = mm.group(2).strip()
                        if url and name:
                            servers.append({"name": name, "url": url})
                    print(f"  extract_servers found: {len(servers)} servers")
                    if not servers:
                        # Try simpler pattern
                        for mm in re.finditer(r'data-embed-url="([^"]+)"', html):
                            print(f"  raw match: {mm.group(1)[:80]}")
                except Exception as ex:
                    print(f"Error: {ex}")
                break
        else:
            continue
        break
    else:
        continue
    break
