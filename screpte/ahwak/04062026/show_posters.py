import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open('scripts/ahwak/data/results_ahwak_moslslat_ramdan_2022.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
titles = ['توبة', 'ظل', 'سكة سفر', 'منحنى خطر', 'يوتيرن', 'ازمة منتصف العمر', 'العاصفة']
for t in titles:
    found = [x for x in data if x['title'].strip() == t]
    if found:
        s = found[0]
        print('%s | %s' % (s['title'], s.get('poster','none')[:120]))
