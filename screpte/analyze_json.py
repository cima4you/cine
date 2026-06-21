#!/usr/bin/env python3
"""Analyze foreign_series_full.json"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

fp = 'D:/Users/DT01/Desktop/rachid-site/scripts/tuktukhd/data/foreign_series_full.json'
with open(fp, 'r', encoding='utf-8') as f:
    t = f.read()

print('Size:', len(t) // 1024, 'KB')
print('Lines:', len(t.splitlines()))

# Try to load as JSON - find error
try:
    data = json.loads(t)
except json.JSONDecodeError as e:
    print('JSON error at line', e.lineno, 'col', e.colno, 'pos', e.pos)
    # Show context around error
    start = max(0, e.pos - 200)
    end = min(len(t), e.pos + 200)
    print('Context:', repr(t[start:end]))

# Count items manually
count = 0
pos = 0
while True:
    pos = t.find('"url"', pos)
    if pos < 0:
        break
    count += 1
    pos += 1
print('Items (by url field):', count)
