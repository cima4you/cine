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

# Show all <li> elements from see.php for this episode
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
see_url = "https://yam.ahwaktv.net/see.php?vid=d235bcda6"
req = urllib.request.Request(see_url, headers=HEADERS)
resp = urllib.request.urlopen(req, timeout=20)
html = resp.read().decode("utf-8", errors="replace")

# Find all <li> elements in the server list area
for m2 in re.finditer(r'<ul[^>]*class="WatchList"[^>]*>(.*?)</ul>', html, re.DOTALL):
    ul_content = m2.group(1)
    print("WatchList UL content:")
    print(ul_content[:2000])
    print("---")

# Also find all <li> with data-embed-url
for m2 in re.finditer(r'<li[^>]*>', html):
    li = m2.group()
    if "embed" in li.lower():
        print(f"LI with embed: {li}")

# Also just look for all li with data-
for m2 in re.finditer(r'<li[^>]*data-[^>]*>', html):
    li = m2.group()
    if "embed" in li.lower():
        print(f"LI data-embed: {li[:300]}")

# Check if there are any li with data-embed-url anywhere
has_direct = re.search(r'<li[^>]*data-embed-url=', html)
print(f"\nHas <li data-embed-url=...> directly: {has_direct is not None}")

# Find data-embed-url outside script tags
no_script = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
for m2 in re.finditer(r'data-embed-url="([^"]+)"', no_script):
    ctx = no_script[max(0,m2.start()-100):m2.end()+50]
    print(f"In non-script: ...{ctx}...")
