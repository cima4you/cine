import requests, re
r = requests.get('https://tuktukhd.com/channel/film-netflix-1/', headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
print('Encoding:', r.encoding)
print('Content-Type:', r.headers.get('Content-Type', ''))
print('Apparent:', r.apparent_encoding)

# Check raw bytes for first alt text
raw = r.content
# Find first alt after first movie-related content
alts_raw = re.findall(r'alt="([^"]+)"'.encode(), raw)
if alts_raw:
    for a in alts_raw[:3]:
        print('Raw alt bytes:', a[:50])
        # Try decoding as utf-8
        try:
            decoded = a.decode('utf-8')
            print('  Decoded:', decoded[:60])
        except:
            print('  NOT utf-8')

# Try extracting from decoded text directly  
alts = re.findall(r'alt="([^"]+)"', r.text)
print('\nDecoded alts:')
for a in alts[:5]:
    print(f'  "{a[:60]}"')
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', a.strip())
    if m:
        print(f'    MATCH: {m.group(1)} ({m.group(2)})')
