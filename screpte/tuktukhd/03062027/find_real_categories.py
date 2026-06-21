import re

with open('scripts/tuktukhd/movie_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find the التصنيفات section - look for what comes after it
# Pattern: التصنيفات followed by category links
idx = html.find('التصنيفات')
if idx > 0:
    section = html[idx:idx+500]
    print('Section around التصنيفات:')
    print(section[:400])
    print()

# Find الانواع section  
idx2 = html.find('الانواع')
if idx2 > 0:
    section2 = html[idx2:idx2+500]
    print('Section around الانواع:')
    print(section2[:400])
    print()

# Find specific category lists/links
# Look for <ul class="category">
cat_list = re.findall(r'<ul[^>]*class="[^"]*(?:category|cat)[^"]*"[^>]*>(.*?)</ul>', html, re.DOTALL)
print('Category lists found: {}'.format(len(cat_list)))
for i, cl in enumerate(cat_list):
    links = re.findall(r'<a[^>]*>([^<]+)</a>', cl)
    print('  List {}: {}'.format(i, links))
