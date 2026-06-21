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
        # Split on Arabic/English boundary
        # Try to find both Arabic and English parts
        # Remove trailing "مترجم" "كامل" etc
        raw = re.sub(r'\s*(مترجم|مدبلج|كامل|اونلاين|وتحميل)\s*$', '', raw)
        # Remove trailing year
        raw = re.sub(r'\s*\d{4}\s*$', '', raw)
        if raw:
            return raw
    # Pattern 2: فيلم ... TITLE  بجودة
    m = re.search(r'فيلم\s+(?:ال[\w]+[\sو]*)*(.+?)\s+بجودة', desc)
    if m:
        raw = m.group(1).strip()
        raw = re.sub(r'\s*(مترجم|مدبلج|كامل|اونلاين)\s*$', '', raw)
        if raw:
            return raw
    # Pattern 3: direct "TITLE" before year
    m = re.search(r'\"(.+?)\"\s*\d{4}', desc)
    if m:
        return m.group(1).strip()
    return None

results = []
for item in items:
    desc = item.get("description", "") or ""
    extracted = extract_title(desc)
    results.append({
        "old_title": item.get("title", ""),
        "extracted_title": extracted,
        "description_preview": desc[:80] + ("..." if len(desc) > 80 else "")
    })
    if extracted:
        item["title"] = extracted

# Save extracted titles reference
with open(INPUT, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

found = sum(1 for r in results if r["extracted_title"])
print(f"Total: {len(items)}, Found titles: {found}, Not found: {len(items)-found}")
print(f"\nSample extractions:")
for r in results[:20]:
    print(f"  '{r['old_title']}' -> '{r['extracted_title']}'  |  {r['description_preview']}")
