import json, re, urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
see_url = "https://yam.ahwaktv.net/see.php?vid=d235bcda6"
req = urllib.request.Request(see_url, headers=HEADERS)
resp = urllib.request.urlopen(req, timeout=20)
html = resp.read().decode("utf-8", errors="replace")

# Print the full HTML to see the structure
print("Full HTML:")
print(html)
