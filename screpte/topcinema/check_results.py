import json
with open('D:\\Users\\DT01\\Desktop\\rachid-site\\scripts\\topcinema\\data\\topcinema_detail.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total = len(data)
with_urls = 0
without_urls = 0
total_servers = 0

for m in data:
    sv = m.get('servers', [])
    total_servers += len(sv)
    has_url = any(s.get('url') for s in sv)
    if has_url:
        with_urls += 1
    else:
        without_urls += 1
        if without_urls <= 3:
            print('No URL servers: {} ({} servers)'.format(m['title'].encode('ascii', 'replace').decode(), len(sv)))

print('\nTotal movies: {}'.format(total))
print('With server URLs: {}'.format(with_urls))
print('Without server URLs: {}'.format(without_urls))
print('Total servers: {}'.format(total_servers))
