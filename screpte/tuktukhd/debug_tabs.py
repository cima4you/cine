import requests, re

url = 'https://tuktukhd.com/series/%D9%85%D8%B3%D9%84%D8%B3%D9%84-from-%D9%85%D8%AA%D8%B1%D8%AC%D9%85/'
html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text

# Find tabContents section
pos = html.find('tabContents')
with open('scripts/tuktukhd/debug_tabs.txt', 'w', encoding='utf-8') as f:
    f.write(html[pos:pos+3000])

print(f"Saved {3000} chars from tabContents")
