#!/usr/bin/env python3
"""Diagnose why foreign-series menu doesn't appear"""
import sys, os, re, json
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'D:/Users/DT01/Desktop/rachid-site'

# 1. Check CATEGORIES in test2.html
fp = os.path.join(BASE, 'RACHID', 'test2.html')
with open(fp, 'r', encoding='utf-8') as f:
    html = f.read()

if 'foreign-series' in html:
    print("[OK] CATEGORIES has foreign-series entry")
else:
    print("[FAIL] CATEGORIES missing foreign-series entry")

# 2. Check data.js for foreign series items
fp = os.path.join(BASE, 'RACHID', 'data.js')
with open(fp, 'r', encoding='utf-8') as f:
    data = f.read()

if 'foreign series appended' in data:
    print("[OK] data.js has foreign series appended")
else:
    print("[FAIL] data.js missing foreign series append")

# Count foreign series items
count = 0
pos = 0
while True:
    pos = data.find('"type": "أجنبي"', pos)
    if pos < 0:
        break
    # Check if contentType follows as series
    chunk = data[pos:pos+500]
    if '"contentType": "series"' in chunk:
        count += 1
    pos += 1

print(f"[INFO] Found {count} foreign series items in data.js")

# 3. Check the rendering logic in test2.html
# Find the renderSections function and the default else case
fp = os.path.join(BASE, 'RACHID', 'test2.html')
with open(fp, 'r', encoding='utf-8') as f:
    html = f.read()

# Check the category filter logic
for section_name, needle in [
    ('CATEGORIES array', "'foreign-series'"),
    ('catLabels', "'foreign-series'"),
    ('others skip exclusion', 'foreign-series'),
]:
    if needle in html:
        print(f"[OK] {section_name} has foreign-series")
    else:
        print(f"[FAIL] {section_name} missing foreign-series")

# Check the default else filter in renderSections
# It should match type=أجنبي + contentType=series
idx = html.find("item.contentType === (cat.contentType || item.contentType)")
if idx > 0:
    print(f"[OK] Default filter found in renderSections")
else:
    print(f"[FAIL] Default filter not found")

# Check the categoryFilter dropdown options
idx = html.find('id="categoryFilter"')
if idx > 0:
    chunk = html[idx:idx+3000]
    if 'foreign-series' in chunk:
        print("[OK] categoryFilter dropdown has foreign-series option")
    else:
        print("[INFO] categoryFilter dropdown might not have foreign-series (auto-generated?)")
        # Check if it's populated from CATEGORIES array
        if 'CATEGORIES.forEach' in html:
            print("[INFO] categoryFilter is populated from CATEGORIES.forEach - should be auto-generated")

# Check for JS errors - try to find if foreign-series is used correctly
# The default else block should match
idx = html.find("} else {")
else_lines = []
lines = html.split('\n')
for i, line in enumerate(lines):
    if '} else {' in line and 'items = contentData.filter' in lines[min(i+1, len(lines)-1)]:
        else_lines.append(i)
        print(f"[INFO] else block at line {i+1}: {lines[i+1].strip()}")

print("\n[SUMMARY]")
print("If all checks pass but menu still doesn't appear:")
print("1. Clear browser cache (Ctrl+F5 / Ctrl+Shift+R)")
print("2. Open browser console (F12) and check for JS errors")
print("3. Check that the 'foreign-series' category in CATEGORIES array")
print("   has matching data items (type=أجنبي, contentType=series)")
