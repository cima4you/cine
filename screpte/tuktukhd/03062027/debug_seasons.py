import requests, re
headers = {'User-Agent': 'Mozilla/5.0'}

url = 'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-erupcja-2026-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/'
r = requests.get(url, timeout=20, headers=headers)
html = r.content.decode('utf-8')

# Check ALL occurrences of "season" or "episode" in the HTML (case-insensitive)
for pattern in ['seasons', 'episodes', 'season', 'episode']:
    matches = re.finditer(r'class="[^"]*{}[^"]*"'.format(pattern), html, re.IGNORECASE)
    count = 0
    for m in matches:
        count += 1
        if count <= 3:
            print('Match: {}'.format(m.group()))
    if count > 3:
        print('  ... and {} more'.format(count - 3))
    print('  Total {}: {}'.format(pattern, count))
