import re, json

t = open('series_page.html', 'r', encoding='utf-8').read()

results = {}
results['has_season_col'] = 'season-col' in t
results['has_episode'] = 'episode' in t

# Find links
links = re.findall(r'href="([^"]+)"', t)
ep_links = [l for l in links if 'episode' in l.lower()]
results['episode_links'] = ep_links[:30]

# Check if we find the word episode in text
ep_mentions = [(m.start(), t[m.start():m.start()+200]) for m in re.finditer(r'episode', t, re.IGNORECASE)]
results['episode_contexts'] = [ctx for _, ctx in ep_mentions[:5]]

# Also look for the end of page
results['last_500_chars'] = t[-500:]

print(json.dumps(results, ensure_ascii=False, indent=2))
