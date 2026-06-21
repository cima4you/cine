import requests, re, json

url = 'https://streamimdb.ru/movie/nqox-your-fault-london'
r = requests.get(url,
  headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
r.encoding = 'utf-8'

text = r.text

results = {}

m = re.search(r'<title>(.*?)</title>', text)
results['title_tag'] = m.group(1).strip() if m else 'NONE'

m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.DOTALL)
results['h1'] = m.group(1).strip() if m else 'NONE'

# Arabic text
arabic = re.findall(r'[\u0600-\u06FF][\u0600-\u06FF\s\u0660-\u0669]{2,}', text)
results['arabic'] = [a.strip() for a in arabic[:10]]

# OG tags
og = re.findall(r'<meta[^>]*og:title[^>]*content="([^"]*)"', text)
results['og_title'] = og[0] if og else 'NONE'

og2 = re.findall(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', text)
results['og_title2'] = og2[0] if og2 else 'NONE'

with open('screpte/streamimdb/data/_detail_check.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('Saved to _detail_check.json')
