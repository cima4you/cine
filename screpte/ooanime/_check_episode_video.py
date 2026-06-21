import requests, re, json

# Check a few episode pages for MP4 URLs
ep_ids = ['10178', '10179', '10180', '10204']
results = {}

for eid in ep_ids:
    url = f'https://www.ooanime.com/episode/{eid}/'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, allow_redirects=True)
    r.encoding = 'utf-8'
    t = r.text
    
    # Check final URL after redirect
    ep = {}
    ep['final_url'] = r.url
    
    # Find video source or iframe
    sources = re.findall(r'<source[^>]*src="([^"]+)"', t)
    ep['sources'] = sources[:3]
    
    iframes = re.findall(r'<iframe[^>]*src="([^"]+)"', t)
    ep['iframes'] = iframes[:3]
    
    # Also check for any video URL in the page
    video_urls = re.findall(r'(https?://[^"\']+\.(mp4|webm|ogg))', t)
    ep['video_urls'] = [v[0] for v in video_urls[:3]]
    
    results[eid] = ep

print(json.dumps(results, ensure_ascii=False, indent=2))
