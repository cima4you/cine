import json, re, urllib.request

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

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Find ALL remaining placeholder episodes and test each
remaining = []
for item in items:
    title = item.get("title", "")
    for s in item.get("seasons", []):
        for e in s.get("episodes", []):
            sv = e.get("servers", [])
            if sv and isinstance(sv, list) and len(sv) > 0 and isinstance(sv[0], dict) and sv[0].get("name") == "watch":
                vid_url = sv[0]["url"]
                m2 = re.search(r"[?&]vid=([0-9a-fA-F]+)", vid_url)
                vid = m2.group(1) if m2 else "N/A"
                remaining.append((title, vid, e.get("episodeNumber","")))

# Test each vid
for title, vid, epnum in remaining:
    try:
        see_url = f"https://yam.ahwaktv.net/see.php?vid={vid}"
        req = urllib.request.Request(see_url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode("utf-8", errors="replace")
        has_iframe = "<iframe" in html
        has_servers = "data-embed-url" in html
        status = f"OK iframe={has_iframe} servers={has_servers} len={len(html)}"
    except urllib.error.HTTPError as ex:
        status = f"HTTP {ex.code}"
    except Exception as ex:
        status = f"ERR {ex}"
    
    print(f"{vid[:8]}.. | {status} | {epnum} | {title[:30]}")

print(f"\nTotal remaining: {len(remaining)}")
