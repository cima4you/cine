import re, json

with open('page.html', 'r', encoding='utf-8') as f:
    t = f.read()

results = {}

# Check for script tags with JSON data
scripts = re.findall(r'<script[^>]*>(.*?)</script>', t, re.DOTALL)
results['script_count'] = len(scripts)
for i, s in enumerate(scripts[:5]):
    results[f'script_{i}_len'] = len(s)
    results[f'script_{i}_start'] = s[:100]

# Check for ajax endpoints or data loading
ajax = re.findall(r'(ajax|fetch|\.load\(|api)', t, re.IGNORECASE)
results['ajax_mentions'] = ajax[:10]

# Look at the main content divs
content_divs = re.findall(r'<div class="([^"]*)"[^>]*>', t)
results['content_divs'] = [c for c in content_divs if 'content' in c.lower() or 'movie' in c.lower() or 'series' in c.lower() or 'episode' in c.lower()][:20]

# Check if page has any series/episode numbers in text
nums = re.findall(r'/\w+/(\d+)/', t)
results['numeric_ids'] = nums[:20]

# Look at the HTML structure around where series might be
sections = re.findall(r'<section[^>]*>(.*?)</section>', t, re.DOTALL)
results['sections'] = len(sections)

# Check for popular/movie sections
popular = re.findall(r'class="[^"]*popular[^"]*"', t)
results['popular_classes'] = popular[:10]

# Find any container with movie/series/cartoon data
containers = re.findall(r'(id|class)="([^"]*(?:movie|series|cartoon|episode)[^"]*)"', t, re.IGNORECASE)
results['containers'] = containers[:20]

print(json.dumps(results, ensure_ascii=False, indent=2))
