import re

with open('scripts/tuktukhd/movie_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find actual category tags/links (not breadcrumb)
# Look for category listing elements
cats = re.findall(r'<a[^>]*href="[^"]*/category/[^"]*"[^>]*>([^<]+)</a>', html)

print('All category-related links:')
for c in cats:
    print('  ', c.strip())

# Check for specific category/tag sections
sections = re.findall(r'(?:تصنيفات|أقسام|فئات|tags|categories)[^:]*:(.*?)</(?:div|section)', html, re.DOTALL | re.IGNORECASE)
print('\nCategory sections:')
for s in sections:
    print('  ', s[:200])

# Look for .category or .cat or .tag classes
tag_items = re.findall(r'class="[^"]*(?:category|cat-item|tag)[^"]*"[^>]*>.*?<a[^>]*>([^<]+)</a>', html)
print('\nCategory/tag items:')
for t in tag_items:
    print('  ', t.strip())

# Check the MasterSingleMeta section more carefully
meta_section = re.search(r'MasterSingleMeta.*?</ul>', html, re.DOTALL)
if meta_section:
    spans = re.findall(r'<span>([^<]*)</span>', meta_section.group())
    print('\nMasterSingleMeta spans:')
    for s in spans:
        print('  ', s.strip())
