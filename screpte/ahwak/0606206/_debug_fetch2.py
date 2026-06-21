import json, re, urllib.request, time

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Test with بنات الشمس vid
test_vids = {
    "بنات الشمس (ep1)": "47a4379a8",
    "بنات الشمس (ep2)": "47a4379a8", # same vid from earlier? no, let me use a different one
}

# Actually let me just test one
vid = "47a4379a8"
see_url = f"https://yam.ahwaktv.net/see.php?vid={vid}"
print(f"Fetching: {see_url}")
req = urllib.request.Request(see_url, headers=HEADERS)
resp = urllib.request.urlopen(req, timeout=30)
html = resp.read().decode("utf-8", errors="replace")
print(f"Got {len(html)} bytes")

# Test iframe extraction
m = re.search(r'<iframe[^>]*src="([^"]+)"', html)
if m:
    print(f"iframe src: {m.group(1)}")
else:
    print("NO iframe found!")

# Test the full extract_servers function
sv = []
for m in re.finditer(r'<li[^>]*data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
    url, name = m.group(1), m.group(2).strip()
    if url and name:
        sv.append({'name': name, 'url': url, 'isDefault': len(sv) == 0})
if not sv:
    for m in re.finditer(r'data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
        url, name = m.group(1), m.group(2).strip()
        if url and name:
            sv.append({'name': name, 'url': url, 'isDefault': len(sv) == 0})
if not sv:
    m = re.search(r'<iframe[^>]*src="([^"]+)"', html)
    if m:
        sv.append({'name': 'Vidspeeds', 'url': m.group(1), 'isDefault': True})
if not sv:
    print("FAILED: no servers found by any method!")
else:
    print(f"Found {len(sv)} servers: {json.dumps(sv, ensure_ascii=False)[:120]}")

# Also check if the fetch function returns anything
print("\n--- Checking fetch ---")
import sys
sys.path.insert(0, r"D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206")
from scrape_turkish_series import fetch_see_page, episode_servers

html2 = fetch_see_page(vid)
if html2:
    print(f"fetch_see_page: {len(html2)} bytes")
else:
    print("fetch_see_page returned None!")

time.sleep(1)
sv2 = episode_servers(f"https://yam.ahwaktv.net/watch.php?vid={vid}")
print(f"episode_servers returned: {json.dumps(sv2, ensure_ascii=False)[:120] if sv2 else 'NONE!'}")
