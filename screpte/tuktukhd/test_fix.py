import sys, json
sys.path.insert(0, 'scripts/tuktukhd')
from scrape_foreign_series import series_detail
det = series_detail('https://tuktukhd.com/series/%D9%85%D8%B3%D9%84%D8%B3%D9%84-from-%D9%85%D8%AA%D8%B1%D8%AC%D9%85/')
with open('scripts/tuktukhd/debug_detail_test.json', 'w', encoding='utf-8') as f:
    json.dump(det, f, ensure_ascii=False, indent=2)
print("Done")
print("Title:", det.get('title', ''))
print("Genres:", det.get('genres', []))
print("Cast:", det.get('cast', []))
print("Seasons:", len(det.get('seasons', [])))
print("Episodes:", len(det.get('episodes', [])))
