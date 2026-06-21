import json, re, os, sys

sc = r"D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206"
sys.path.insert(0, sc)
from scrape_turkish_series import load_json, to_site_format

full = load_json(os.path.join(sc, "data", "turkish_series_full.json"))
converted = to_site_format(full)

targets = ["قيامة عثمان", "الشتاء الاسود", "شتاء اسود", "طائر الرفراف", "البطل"]
for item in converted:
    t = item.get("title", "")
    for target in targets:
        if target in t:
            print(f"Found: {t}")
            for s in item.get("seasons", []):
                for e in s.get("episodes", []):
                    sv = e.get("servers", [])
                    epn = e.get("episodeNumber", "")
                    if sv:
                        print(f"  Ep {epn}: {sv[0].get('name','')} len={len(sv)}")
                    else:
                        print(f"  Ep {epn}: EMPTY servers")
            break
