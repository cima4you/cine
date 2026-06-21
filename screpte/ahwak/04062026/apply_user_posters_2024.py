import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])
prefix = c[:c.index('[')]
suffix = c[c.rindex(']')+1:]

# Poster mappings: title -> poster_url
posters = {
    'اعلى نسبة مشاهدة': 'https://media0101.elcinema.com/uploads/_315x420_70dc8f13c36b6244193811f37fe16ad64c56c0e6bdfb4ca2552bb98b4be51fe9.jpg',
    'الصديقات': 'https://media0101.elcinema.com/uploads/_315x420_361f24b5f2c4e1dbc4d1a87d83f6ee86311588ac5680ae40feea19ebc788e6b1.jpg',
    'بـ١٠٠ راجل': 'https://media0101.elcinema.com/uploads/_315x420_73bea89c4d7d257e8d672d94a821ee126cf82b151769b18e561c62747b6594b5.jpg',
    'تل الراهب': 'https://media0101.elcinema.com/uploads/_315x420_59663599f0d49b143357595321d17084cc5cefaf1db8e6d9a142f71cc0e66be6.jpg',
    'اغمض عينيك': 'https://media0101.elcinema.com/uploads/_315x420_da99f5d88e3b389f70b15014b771a23e3646d7226a52bf44ebe7e0da13e3b593.jpg',
    'العائلة اكس': 'https://media0101.elcinema.com/uploads/_315x420_eda3da02c67b9ed50fbb13bab6b8285c5cf1ddec1650d28a5966ff1b6c14a0a6.jpg',
    'الف ليلة وليلة': 'https://media0101.elcinema.com/uploads/_315x420_44fb9cd586012ab965606fec8d0c936beaef87b133aa5c47c704845897ebc734.jpg',
    'لفرج بعد الشدة': 'https://media0101.elcinema.com/uploads/_315x420_89a593fd7149a98feb3deaeeb1d9613f592bf15d7aca7cf1e9cf4a5e78866353.jpg',
    'الوشم': 'https://media0101.elcinema.com/uploads/_315x420_e4c78a187f03f6de348f1bdbaac5599a2298a0e00aeb0a1608b3acf89258de37.jpg',
    'رحيل': 'https://media0101.elcinema.com/uploads/_315x420_d72a175b1f6ec0251d638d8cbc4681bf2e7a138746c1b8d65d57a2a3bb5f0ef2.jpg',
    'فراولة': 'https://media0101.elcinema.com/uploads/_315x420_c93ee6ea6e7cb9508ecc8ce16ea57d426103787fc78c49ef46fd3289b4c9159d.jpg',
    'قلم رصاص': 'https://media0101.elcinema.com/uploads/_315x420_6f6497981afa713714a8e7ca92deaf38f50f71c2dfe5060b45f7c4503b7e5b51.jpg',
    'كوبرا': 'https://media0101.elcinema.com/uploads/_315x420_6f320795717b2e4de579ff4ed0c74701baf7887b7fc0b31c4db1761f7a077ee6.jpg',
    'محارب': 'https://media0101.elcinema.com/uploads/_315x420_eff4dbfe0ee39d29124d40ddd50ddb204ba6bdc3458e6fecde0891c474c5c636.jpg',
    'ياهلي': 'https://media0101.elcinema.com/uploads/_315x420_bb17d54b338332551f17561458c8a9a31e0219957939b5d2996dedbd0ef40700.jpg',
}

# Handle الصديقات (القطط) - same poster as الصديقات
# Also handle "الف ليلة وليلة: جودر" matching "الف ليلة وليلة"

found = 0
not_found = 0
matches_detail = []

for title_key, poster_url in posters.items():
    # Find matching items in data - try exact or partial match on title, year=2024
    matching = []
    for i, item in enumerate(data):
        item_title = item.get('title', '')
        item_year = item.get('year', '')
        # Check if title_key is contained in item_title or vice versa
        if (title_key in item_title or item_title in title_key) and item_year == '2024':
            matching.append((i, item_title))

    if len(matching) == 0:
        # Try without year filter
        for i, item in enumerate(data):
            item_title = item.get('title', '')
            if title_key in item_title or item_title in title_key:
                matching.append((i, item_title))
        if matching:
            matches_detail.append((title_key, 'found_no_year', matching, poster_url))
        else:
            matches_detail.append((title_key, 'not_found', [], poster_url))
        not_found += 1
    elif len(matching) == 1:
        idx, item_title = matching[0]
        old = data[idx].get('poster', '')[:60]
        data[idx]['poster'] = poster_url
        matches_detail.append((title_key, 'ok', [(idx, item_title, old)], poster_url))
        found += 1
    else:
        # Multiple matches - use exact match first
        exact = [(i, t) for i, t in matching if t == title_key]
        if exact:
            idx, item_title = exact[0]
            old = data[idx].get('poster', '')[:60]
            data[idx]['poster'] = poster_url
            matches_detail.append((title_key, 'ok_exact', [(idx, item_title, old)], poster_url))
            found += 1
        else:
            matches_detail.append((title_key, 'multiple', matching, poster_url))
            not_found += 1

print('Results:')
for title_key, status, detail, url in matches_detail:
    if status == 'ok' or status == 'ok_exact':
        idx, item_title, old = detail[0]
        print('  OK: %s -> %s (was: %s)' % (title_key, item_title[:30], old[:40]))
    elif status == 'found_no_year':
        print('  NO YEAR: %s matched %s but year is not 2024' % (title_key, [(i, t) for i, t in detail]))
    elif status == 'not_found':
        print('  MISS: %s - no match in data.js' % title_key)
    elif status == 'multiple':
        print('  MULTI: %s matches: %s' % (title_key, [(i, t) for i, t in detail]))

print('\nFound: %d, Not found: %d' % (found, not_found))

# Write back
json_str = json.dumps(data, ensure_ascii=False)
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('data.js updated')
