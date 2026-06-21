import re
with open('D:\\Users\\DT01\\Desktop\\rachid-site\\scripts\\topcinema\\debug_watch_personhood.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Try the exact regex from the main script
pattern1 = r'<li[^>]*data-id="(\d+)"[^>]*data-server="(\d+)"[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>(.*?)</span>'
matches1 = re.findall(pattern1, html, re.DOTALL)
print('Pattern 1 (with class):', len(matches1))

pattern2 = r'<li[^>]*data-id="(\d+)"[^>]*data-server="(\d+)"[^>]*>.*?<span>(.*?)</span>'
matches2 = re.findall(pattern2, html, re.DOTALL)
print('Pattern 2 (without class):', len(matches2))

# Show the actual HTML around the server items
watch_area = re.search(r'watch--servers--list.*?<ul>(.*?)</ul>', html, re.DOTALL)
if watch_area:
    ul_content = watch_area.group(1)
    print('Watch area ul content ({} chars):'.format(len(ul_content)))
    print(ul_content[:2000])
