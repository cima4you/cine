import sys, json
sys.stdout.reconfigure(encoding='utf-8')

AHWAK_FILE = 'scripts/ahwak/data/results_ahwak_moslslat_ramdan_2022.json'
DATA_JS = 'data.js'

# Correct work IDs and poster URLs for each series
corrections = {
    'توبة': 'https://media0101.elcinema.com/uploads/_315x420_49f93486b88d0628d58650298ffa9265b914776c6f9abf1b3a2eadc366727752.jpg',
    'ظل': 'https://media0101.elcinema.com/uploads/_315x420_078b2e1e20373f6fbb9d1e2380c6539e2f7a381ffea5bb60993657f70e6c661d.jpg',
    'سكة سفر': 'https://media0101.elcinema.com/uploads/_315x420_f6f027c2f5e53122ff8d40622ced26cdb24dac49027f0caecfbe3cc047432ff7.jpg',
    'يوتيرن': 'https://media0101.elcinema.com/uploads/_315x420_ce475ebe50ed91c14cf68cb308422153ec4136ddfceaf696a39850fb3bcec38c.jpg',
    'ازمة منتصف العمر': 'https://media0101.elcinema.com/uploads/_315x420_c655a3ab2925e91483c878e3f78d7ae36be81fe53ba203cdfb5c760bedd691e3.jpg',
    'منعطف خطر': 'https://media0101.elcinema.com/uploads/_315x420_e0a67295aed8e79ac947b1f6a5143a041e4d320b0096290d5649731df25f2fe4.jpg',
    'عاصفة': 'https://media0101.elcinema.com/uploads/_315x420_a2fec0cda8dd6a58da63eab7776821bf6df8ad518a01617869b22ea1acc4e8e6.jpg',
}

# Renames
renames = {
    'منحنى خطر': 'منعطف خطر',
    'العاصفة': 'عاصفة',
}

# Update ahwak results
with open(AHWAK_FILE, 'r', encoding='utf-8') as f:
    ahwak = json.load(f)

for i, s in enumerate(ahwak):
    title = s['title'].strip()
    
    # Apply renames
    if title in renames:
        ahwak[i]['title'] = renames[title]
        print('Renamed: %s -> %s' % (title, renames[title]))
        title = renames[title]  # use new name for poster lookup
    
    # Apply poster corrections
    if title in corrections:
        old = s.get('poster', '')
        ahwak[i]['poster'] = corrections[title]
        print('Poster corrected: %s' % title)

with open(AHWAK_FILE, 'w', encoding='utf-8') as f:
    json.dump(ahwak, f, ensure_ascii=False, indent=2)
print('\nSaved ahwak results.')

# Update data.js
with open(DATA_JS, 'r', encoding='utf-8') as f:
    c = f.read()
arr_start = c.index('[')
arr_end = c.rindex(']') + 1
data = json.loads(c[arr_start:arr_end])
prefix = c[:arr_start]
suffix = c[arr_end:]

updated = 0
for i, item in enumerate(data):
    title = item.get('title', '').strip()
    
    # Apply renames
    if title in renames:
        data[i]['title'] = renames[title]
        print('data.js Renamed: %s -> %s' % (title, renames[title]))
        title = renames[title]
    
    # Apply poster corrections
    if title in corrections:
        data[i]['poster'] = corrections[title]
        updated += 1
        print('data.js Poster corrected: %s' % title)

print('\nUpdated %d items in data.js' % updated)

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Saved data.js.')
