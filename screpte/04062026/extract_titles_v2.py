import re, json, sys
sys.stdout.reconfigure(encoding="utf-8")

INPUT = r"D:\Users\DT01\Desktop\rachid-site\placeholder_2026_items.json"

with open(INPUT, "r", encoding="utf-8") as f:
    items = json.load(f)

def extract_title(desc):
    if not desc:
        return None
    # Pattern 1: فيلم ... TITLE 2026
    m = re.search(r'فيلم\s+(?:ال[\w]+[\sو]*)*(.+?)\s+2026', desc)
    if m:
        raw = m.group(1).strip()
        raw = re.sub(r'\s*(مترجم|مدبلج|كامل|اونلاين|وتحميل)\s*$', '', raw)
        raw = re.sub(r'\s*\d{4}\s*$', '', raw)
        if raw:
            return raw
    # Pattern 2: فيلم ... TITLE بجودة
    m = re.search(r'فيلم\s+(?:ال[\w]+[\sو]*)*(.+?)\s+بجودة', desc)
    if m:
        raw = m.group(1).strip()
        raw = re.sub(r'\s*(مترجم|مدبلج|كامل|اونلاين)\s*$', '', raw)
        if raw:
            return raw
    # Pattern 3: "TITLE" (+year)
    m = re.search(r'\"(.+?)\"\s*\d{4}', desc)
    if m:
        return m.group(1).strip()
    return None

# Also try to detect duplicate descriptions to group them
desc_groups = {}
for i, item in enumerate(items):
    desc = (item.get("description", "") or "").strip()
    if desc:
        # Use first 100 chars as key for grouping
        key = desc[:100]
        if key not in desc_groups:
            desc_groups[key] = []
        desc_groups[key].append(i)

print(f"Unique descriptions: {len(desc_groups)} out of {len(items)} items")

# Show groups with count > 1 (duplicates)
dups = {k: v for k, v in desc_groups.items() if len(v) > 1}
print(f"\nDuplicate description groups ({len(dups)}):")
for k, indices in sorted(dups.items(), key=lambda x: -len(x[1])):
    print(f"  [{len(indices)}x] {k[:60]}...")

# Now extract titles
found = 0
for item in items:
    desc = item.get("description", "") or ""
    extracted = extract_title(desc)
    if extracted:
        item["title"] = extracted
        found += 1

with open(INPUT, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"\nExtracted titles: {found}")
print(f"Still untitled: {len(items) - found}")
