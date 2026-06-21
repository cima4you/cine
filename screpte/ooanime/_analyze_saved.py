import re, json

with open('page.html', 'r', encoding='utf-8') as f:
    t = f.read()

results = {}

# Unique series
series_ids = sorted(set(re.findall(r'/series/(\d+)/', t)))
results['unique_series'] = series_ids
results['series_count'] = len(series_ids)

# Check the structure - look for the series grid/listing
# Find the container that holds all series
sections = re.findall(r'<div class="rgt tcb-product-item content"[^>]*>.*?</div>\s*</div>\s*</div>', t, re.DOTALL)
results['direct_content_blocks'] = len(sections)

# Extract title, link, poster for each series
item_pattern = r'<a href="(https://www\.ooanime\.com/series/\d+/[^"]+)"[^>]*>\s*<img[^>]*src="([^"]+)"[^>]*>'
items = re.findall(item_pattern, t)
results['items_with_links_imgs'] = [(link, img) for link, img in items]

# Check for alt text
alts = re.findall(r'<img[^>]*src="https://www\.ooanime\.com/files/[^"]+"[^>]*alt="([^"]*)"', t)
results['alts'] = alts[:5]

# Get series data from the content-mov section
content_mov = re.findall(r'<div class="rgt content-mov"[^>]*>(.*?)</div>', t, re.DOTALL)
results['content_mov_count'] = len(content_mov)

# Get name from URL
series_data = []
for sid in set(re.findall(r'/series/(\d+)/([^"\'?]+)', t)):
    series_data.append({'id': sid[0], 'name': sid[1]})
results['series_data'] = series_data

# Check if there's a different section with more cartoons
# Look at full HTML structure around the series listing
popular_sections = re.findall(r'popular[^>]*>', t)
results['popular_sections'] = popular_sections[:10]

# Check for "cartoon" category specifically  
cartoon_section = re.findall(r'class="[^"]*cartoon[^"]*"[^>]*>', t)
results['cartoon_classes'] = cartoon_section[:10]

# Also check for kategori filter links
filter_links = re.findall(r'href="(/tvseries\?category=[^"]+)"', t)
results['filter_links'] = filter_links[:20]

print(json.dumps(results, ensure_ascii=False, indent=2))
