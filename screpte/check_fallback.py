import re, sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Users\DT01\Desktop\rachid-site\test\data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find entries whose year field is or matches to 2073, 2039, 1881, 1945, etc.
# that could still appear after the fix
# These might be coming from the fallback: title regex match

# Find entries that could contribute "bad" years via the title fallback
# First check movie "1881"
m = re.search(r'"title":\s*"1881"', content)
if m:
    print("Movie '1881' found in data.js")
else:
    print("No movie '1881'")

m = re.search(r'"title":\s*"2039"', content)
if m:
    print("Movie '2039' found in data.js")
else:
    print("No movie '2039'")

# Check what years would appear in the dropdown (unique sorted years)
# from the year field (after fix) + title fallback
years_set = set()

# Get years from the year field
for m in re.finditer(r'"year":\s*"(\d*)"', content):
    y = m.group(1)
    if y:
        years_set.add(y)

# Get years from title fallback for entries without year
# Rough check: find entries without year field but with 4-digit year in title
# This is harder to do via regex on raw text, let's check some specific values
for y in ['1881', '1945', '2039', '2073']:
    m = re.search(r'"year":\s*""', content)
    if m and re.search(r'"title":\s*"' + y + r'"', content):
        print(f"Movie titled '{y}' with empty year -> would show as year '{y}' in dropdown")
    elif re.search(r'"title":\s*"' + y + r'"', content):
        # Check if it has a year field
        yr_match = re.search(r'"title":\s*"' + y + r'".*?"year":\s*"([^"]*)"', content)
        if yr_match:
            print(f"Movie '{y}' has year='{yr_match.group(1)}'")
        else:
            print(f"Movie '{y}' - no year field")
    else:
        print(f"Movie titled '{y}' not found in data")
