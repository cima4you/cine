import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'larozza', 'data')
results_dir = os.path.normpath(results_dir)

files = [f for f in os.listdir(results_dir) if f.startswith('results_larozza_') and f.endswith('.json')]
if not files:
    print('ما لقيتش ملفات نتائج في:', results_dir)
    sys.exit(1)

for fname in sorted(files):
    fpath = os.path.join(results_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print('=' * 60)
    print(f'الملف: {fname}')
    print('=' * 60)
    print()

    total_series = len(data)
    total_eps = 0
    total_servers = 0
    series_data = []

    for s in data:
        title = s['title']
        eps = s['seasons'][0]['episodes']
        num_eps = len(eps)
        num_servers = sum(len(e['servers']) for e in eps)
        ep_nums = [e['episodeNumber'] for e in eps]
        total_eps += num_eps
        total_servers += num_servers
        cats = ', '.join(s['categories'])
        series_data.append((title, num_eps, num_servers, ep_nums, cats))

    print(f'إجمالي المسلسلات: {total_series}')
    print(f'إجمالي الحلقات:   {total_eps}')
    print(f'إجمالي السيرفرات: {total_servers}')
    print(f'متوسط السيرفرات:  {total_servers // total_eps} لكل حلقة')
    print()

    # Top 5 most episodes
    print('--- أكثر 5 مسلسلات حلقات ---')
    for title, num_eps, num_servers, ep_nums, cats in sorted(series_data, key=lambda x: -x[1])[:5]:
        print(f'  {title}: {num_eps} حلقة, {num_servers} سيرفر')
    print()

    # Bottom 5 least episodes
    print('--- أقل 5 مسلسلات حلقات ---')
    for title, num_eps, num_servers, ep_nums, cats in sorted(series_data, key=lambda x: x[1])[:5]:
        print(f'  {title}: {num_eps} حلقة')
    print()

    # Categories breakdown
    cats_count = {}
    for s in data:
        for c in s['categories']:
            cats_count[c] = cats_count.get(c, 0) + 1
    print('--- التصنيفات ---')
    for c, n in sorted(cats_count.items(), key=lambda x: -x[1]):
        print(f'  {c}: {n} مسلسل')
    print()

    # All series list
    print('--- جميع المسلسلات ---')
    for title, num_eps, num_servers, ep_nums, cats in series_data:
        ep_range = f'{ep_nums[0]}-{ep_nums[-1]}' if num_eps > 1 else str(ep_nums[0])
        print(f'  {title}: {ep_range} ({num_eps})')
