import re, sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\Users\DT01\Desktop\rachid-site\test\data.js', 'r', encoding='utf-8') as f:
    content = f.read()

all_years = [m.group(1) for m in re.finditer(r'"year":\s*"(\d*)"', content)]
c = Counter(all_years)

total = sum(c.values())
empty = c.get("", 0)
valid = sum(v for y, v in c.items() if y and 1888 <= int(y) <= 2026)
invalid = total - empty - valid

print(f"Total year fields: {total}")
print(f"Empty years: {empty}")
print(f"Valid (1888-2026): {valid}")
print(f"Invalid: {invalid}")

if invalid > 0:
    print("\nRemaining invalid years:")
    for y in sorted(c.keys()):
        if y and not (1888 <= int(y) <= 2026):
            count = c[y]
            bar = "#" * min(count, 50)
            print(f"  {y}: {count} {bar}")
