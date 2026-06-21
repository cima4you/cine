import requests, re, json, base64

headers = {'User-Agent': 'Mozilla/5.0'}

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

# Manual mappings: title, year -> tuktukhd URL
manual_matches = [
    ('Blue Cave', '2024', 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-%D8%A7%D9%84%D9%83%D9%87%D9%81-%D8%A7%D9%84%D8%A7%D8%B2%D8%B1%D9%82-mavi-magara-2024-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'),
    ('My Hero Academia: You\'re Next', '2024', 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-boku-no-hero-academia-the-movie-4-youre-next-2024-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'),
    ('Haiky\u016b!! La Guerre des poubelles', '2024', 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-haikyuu-movie-gomisuteba-no-kessen-2024-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'),
    ('2 Sailor Moon Cosmos Part', '2023', 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-pretty-guardian-sailor-moon-cosmos-the-movie-part-2-2024-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'),
    ('Mononoke Paper Umbrella', '2024', 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-mononoke-movie-karakasa-2024-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'),
]

# Find indices
updates = []
for idx, item in enumerate(data_js):
    title = item.get('title', '').strip()
    year = str(item.get('year', ''))
    for mt, my, url in manual_matches:
        if title == mt and year == my:
            if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
                updates.append({'idx': idx, 'title': title, 'year': year, 'url': url})
                break

print('Items to update: {}'.format(len(updates)))
for u in updates:
    print('  "{}" ({}) [idx={}] -> {}'.format(u['title'], u['year'], u['idx'], u['url'][:80]))

if updates:
    print('\nVisiting pages...')
    updated = 0
    for u in updates:
        try:
            r = requests.get(u['url'], timeout=20, headers=headers)
            crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
            watch_urls = [base64.b64decode(c).decode('utf-8') for c in crypts]
            dl_links = re.findall(r'data-real-url="([^"]+)"', r.text)
            si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', r.text, re.DOTALL)
            sname = si[0].strip() if si else 'TukTuk Vip'
            
            if watch_urls:
                item = data_js[u['idx']]
                new_server = {'name': sname, 'url': watch_urls[0], 'isDefault': True}
                new_downloads = [{'name': 'TukTuk Download', 'url': dl} for dl in dl_links]
                
                old_servers = item.get('servers', [])
                item['servers'] = [s for s in old_servers if s.get('name', '') not in target_servers]
                item['servers'].insert(0, new_server)
                
                if new_downloads:
                    item['downloadServers'] = new_downloads
                updated += 1
                print('  UPDATED: "{}"'.format(u['title']))
            else:
                print('  FAILED: no watch URL for "{}"'.format(u['title']))
        except Exception as e:
            print('  ERROR: "{}" - {}'.format(u['title'], str(e)))
    
    print('\nUpdated: {} items'.format(updated))
    
    if updated > 0:
        prefix = content[:content.index('[')]
        suffix = content[content.rindex(']') + 1:]
        json_str = json.dumps(data_js, ensure_ascii=False)
        with open('data.js', 'w', encoding='utf-8') as f:
            f.write(prefix + json_str + suffix)
        print('Saved data.js')
    
    final_remaining = sum(1 for item in data_js if any(s.get('name', '') in target_servers for s in item.get('servers', [])))
    print('Final remaining multi-quality servers: {}'.format(final_remaining))
