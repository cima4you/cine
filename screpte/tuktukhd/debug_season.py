import requests, re, json

r = requests.get('https://tuktukhd.com/series/%D9%85%D8%B3%D9%84%D8%B3%D9%84-from-%D9%85%D8%AA%D8%B1%D8%AC%D9%85/', 
    headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

result = {}
result['has_allseasonsss'] = 'allseasonsss' in html

# Check for season containers
season_divs = []
for m in re.finditer(r'<(section|div)[^>]*class="[^"]*season[^"]*"', html):
    season_divs.append(m.group())
result['season_containers'] = season_divs

# Find ALL h3 elements near the content
h3_with_season = []
for m in re.finditer(r'<h3>([^<]*\u0627\u0644\u0645\u0648\u0633\u0645[^<]*)</h3>', html):
    h3_with_season.append(m.group(1))

result['h3_seasons'] = h3_with_season

# Check div with class MasterSingleMeta
result['has_master'] = 'MasterSingleMeta' in html

# Search for seasons around the content
# Let's look for the section that contains the seasons
result['around_season_1'] = ''
pos = html.find('\u0627\u0644\u0645\u0648\u0633\u0645 1')
if pos >= 0:
    result['around_season_1'] = html[max(0,pos-100):pos+200]

with open('scripts/tuktukhd/debug_season.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("Saved")
