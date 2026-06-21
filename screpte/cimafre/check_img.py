import requests
r = requests.get('https://cumafree.onl/uploads/thumbs/924956628-1.jpg',
                 headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://cimafre.site/'},
                 timeout=10)
print(f'{r.status_code}, {len(r.content)}b, Content-Type: {r.headers.get("content-type","")}')
