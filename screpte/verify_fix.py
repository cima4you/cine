import re, sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Users\DT01\Desktop\rachid-site\test\data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find entries with year field - check a few
# Find "year":"8217" specifically (exact match)
matches = list(re.finditer(r'"year":\s*"(\d+)"', content))
bad = [(m.group(0), m.group(1)) for m in matches if m.group(1) and not (1888 <= int(m.group(1)) <= 2026)]

if bad:
    print(f"❌ Found {len(bad)} bad years still in file:")
    for text, year in bad[:10]:
        print(f"   {text}")
else:
    print("✅ No bad years found in data.js")

# Also verify the total count
total_year_fields = len(matches)
print(f"Total year fields: {total_year_fields}")
