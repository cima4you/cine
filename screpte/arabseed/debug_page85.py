import requests, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding="utf-8")
from bs4 import BeautifulSoup
from urllib.parse import unquote

url = "https://m.asd.ink/category/turkish-series-2/page/85/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
}
r = requests.get(url, headers=headers, verify=False, timeout=30)
soup = BeautifulSoup(r.text, "html.parser")
items = soup.select("li.box__xs__2")
print(f"Total items: {len(items)}")
for li in items[:5]:
    a = li.select_one("a.movie__block")
    if a:
        href = a.get("href","")
        cls = a.get("class",[])
        title = a.get("title","")
        img = li.select_one("img.images__loader")
        poster = img.get("data-src","") if img else ""
        print(f"\nhref: {unquote(href)[:80]}")
        print(f"class: {cls}")
        print(f"title: {title[:60]}")
        print(f"is_episode: {'is__episode' in cls}")
        print(f"poster: {poster[:60] if poster else 'N/A'}")
    else:
        print("No a.movie__block found")
