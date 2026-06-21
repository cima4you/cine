#!/usr/bin/env python3
"""Verify foreign-series integration into all site files"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'D:/Users/DT01/Desktop/rachid-site'
checks = {
    'split/index.html': [
        ('CATEGORIES entry', "'foreign-series'"),
        ('script tag', 'data-foreign-series.js'),
        ('catLabels', "'foreign-series'"),
        ('others skip', 'foreign-series'),
        ('others return', 'foreign-series'),
        ('turkish_scroll', 'foreign-series'),
    ],
    'RACHID/test2.html': [
        ('CATEGORIES entry', "'foreign-series'"),
        ('others skip', 'foreign-series'),
        ('others return', 'foreign-series'),
        ('catLabels', "'foreign-series'"),
        ('turkish_scroll', 'foreign-series'),
    ],
    'test/test2.html': [
        ('CATEGORIES entry', "'foreign-series'"),
        ('others skip', 'foreign-series'),
        ('others return', 'foreign-series'),
        ('catLabels', "'foreign-series'"),
        ('turkish_scroll', 'foreign-series'),
    ],
    'RACHID/data.js': [('appended', 'foreign series appended')],
    'test/data.js': [('appended', 'foreign series appended')],
    'split/data-loader.js': [('cd_foreign_series', 'cd_foreign_series')],
}

ok = True
for fname, clist in checks.items():
    fp = os.path.join(BASE, fname)
    if not os.path.exists(fp):
        print(f'MISSING: {fname}')
        ok = False; continue
    with open(fp, 'r', encoding='utf-8') as f:
        c = f.read()
    for label, kw in clist:
        if kw not in c:
            print(f'FAIL: {fname} - {label}')
            ok = False
if ok:
    print('ALL CHECKS PASSED')
else:
    print('SOME CHECKS FAILED')
