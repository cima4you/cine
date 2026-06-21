import json, re, urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Test المؤسس عثمان ep 76
vid = "b76410d51"
see_url = f"https://yam.ahwaktv.net/see.php?vid={vid}"
req = urllib.request.Request(see_url, headers=HEADERS)
resp = urllib.request.urlopen(req, timeout=20)
html = resp.read().decode("utf-8", errors="replace")
print(f"Length: {len(html)}")

# Find ALL data-embed-url occurrences
count = 0
for m in re.finditer(r'data-embed-url="([^"]+)"', html):
    ctx = html[max(0,m.start()-80):m.end()+80]
    count += 1
    print(f"\n--- #{count} ---")
    print(f"URL: {m.group(1)[:100]}")
    print(f"Ctx: {ctx}")

if count == 0:
    print("NO data-embed-url found in HTML!")
    # Check for iframe
    m = re.search(r'<iframe[^>]*src="([^"]+)"', html)
    if m:
        print(f"iframe src: {m.group(1)}")
    else:
        print("No iframe either")
        # Show relevant part of HTML
        idx = html.find("Playerholder")
        if idx >= 0:
            print(html[idx:idx+500])
