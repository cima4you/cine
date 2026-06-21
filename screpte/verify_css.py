#!/usr/bin/env python3
"""Verify foreign-series-card CSS + JS changes"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'D:/Users/DT01/Desktop/rachid-site'
checks = {
    'split/index.html': [
        ('JS: isForeignSeries', 'isForeignSeries'),
        ('JS: foreign-series-card class', 'foreign-series-card'),
        ('CSS: foreign-series-card rule', 'foreign-series-card .poster-wrapper'),
    ],
    'RACHID/test2.html': [
        ('JS: isForeignSeries', 'isForeignSeries'),
        ('JS: foreign-series-card class', 'foreign-series-card'),
        ('CSS: foreign-series-card rule', 'foreign-series-card .poster-wrapper'),
    ],
    'test/test2.html': [
        ('JS: isForeignSeries', 'isForeignSeries'),
        ('JS: foreign-series-card class', 'foreign-series-card'),
        ('CSS: foreign-series-card rule', 'foreign-series-card .poster-wrapper'),
    ],
}

ok = True
for fname, clist in checks.items():
    fp = os.path.join(BASE, fname)
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
