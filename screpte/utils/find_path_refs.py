import os, re

script_dir = 'scripts'
for f in sorted(os.listdir(script_dir)):
    if f.endswith('.py'):
        fp = os.path.join(script_dir, f)
        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
        refs = re.findall(r"['\"](scripts/tuktuk_[^'\"]+)['\"]|['\"](data/[^'\"]+)['\"]|['\"](scripts/results_[^'\"]+)['\"]", content)
        if refs:
            print('{}:'.format(f))
            for r in refs:
                print('  -> {}'.format(r[0] if r[0] else (r[1] if r[1] else r[2])))
