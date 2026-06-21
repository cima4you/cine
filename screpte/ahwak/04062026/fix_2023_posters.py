import sys, json
sys.stdout.reconfigure(encoding='utf-8')

AHWAK_FILE = 'scripts/ahwak/data/results_yam_moslslat_ramdan_2023.json'
DATA_JS = 'data.js'

corrections = {
    'العربجي': 'https://media0101.elcinema.com/uploads/_315x420_5d6b930ac0b190e98aaaa3cf53e899189e3ce666b9179e79d93129c772b68f3a.jpg',
    'اقتحام': 'https://media0101.elcinema.com/uploads/_315x420_cdd9b27dcd68696e2b200e04676ee85f088dc1cca11d65468e19849dbe084790.jpg',
    'الخوات': 'https://media0101.elcinema.com/uploads/_315x420_7746a6c2c7896a186ff0be76ee8182916203c7c0062b00dccf4e6c194f797000.jpg',
    'الشرار': 'https://media0101.elcinema.com/uploads/_315x420_3dc9bcc342240c5f75a0310daa4f4b66fd23bb79b77adb94bb8c63dd348de915.jpg',
    'الصندوق': 'https://media0101.elcinema.com/uploads/_315x420_1d230bc403f0adcc1a34ffd3d5b70343d6b7bf16623ac40cadf7a69e8b2383c8.jpg',
    'الكرزون': 'https://media0101.elcinema.com/uploads/_315x420_a80e701a321c12bef6bc128bca9bd4736275fcb28e28df2a72b1c7120491d5a1.jpg',
    'جت سليمة': 'https://media0101.elcinema.com/uploads/_315x420_fb694a97121bfebc3cbcbf9942d2fc440c80c0dccfceb4bdcf4a0d40bb08109d.jpg',
    'جميلة': 'https://media0101.elcinema.com/uploads/_315x420_3bbf41a57e949e22e771672100aadc35edf1a8d68e5a208717b2bb7256dd8ad8.jpg',
    'رسالة الامام': 'https://media0101.elcinema.com/uploads/_315x420_0dbb77226cb1a1d5659e30d76277afb66096bab88a559149f0339ed533c28aba.jpg',
    'زقاق الجن': 'https://media0101.elcinema.com/uploads/_315x420_5a7b844e291ef369964e880c716bab9acd55493bc696f5d1ff4130e76e6b217f.jpg',
    'عودة البارون': 'https://tye.txcima.com/wp-content/uploads/2023/03/315x420_faa1fdfd169e48527636f7a182f03bd7b219d1040e6105d0ba1798de56d683ed.jpg',
    'عملة نادرة': 'https://media0101.elcinema.com/uploads/_315x420_0e2d681ba4e7ccfb54f8b856bcd62429aab3fb25b20521e2d3748d29a0bb2d5e.jpg',
}

# Update ahwak results
with open(AHWAK_FILE, 'r', encoding='utf-8') as f:
    ahwak = json.load(f)

for i, s in enumerate(ahwak):
    t = s['title'].strip()
    if t in corrections:
        ahwak[i]['poster'] = corrections[t]
        print('Fixed: %s' % t)

with open(AHWAK_FILE, 'w', encoding='utf-8') as f:
    json.dump(ahwak, f, ensure_ascii=False, indent=2)
print('Saved ahwak results.')

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
    t = item.get('title', '').strip()
    if t in corrections:
        data[i]['poster'] = corrections[t]
        updated += 1

print('Updated %d items in data.js' % updated)
json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Saved data.js.')
