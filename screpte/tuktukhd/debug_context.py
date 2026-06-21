import requests, re, json

url = 'https://tuktukhd.com/series/%D9%85%D8%B3%D9%84%D8%B3%D9%84-from-%D9%85%D8%AA%D8%B1%D8%AC%D9%85/'
html = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text

pos = html.find('allseasons')
# Extract 300 chars around it
start = max(0, pos - 100)
end = min(len(html), pos + 200)

with open('scripts/tuktukhd/debug_context.txt', 'w', encoding='utf-8') as f:
    f.write(f"Position: {pos}\n")
    f.write(f"Context ({start}-{end}):\n")
    f.write(html[start:end])
    
print(f"Saved context for 'allseasons' at position {pos}")
print(f"Total HTML length: {len(html)}")
