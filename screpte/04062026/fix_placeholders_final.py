import re, json, sys
sys.stdout.reconfigure(encoding="utf-8")

INPUT = r"D:\Users\DT01\Desktop\rachid-site\placeholder_2026_items.json"

with open(INPUT, "r", encoding="utf-8") as f:
    items = json.load(f)

def clean_title(raw):
    """Extract English title from mixed Arabic/English; fallback to cleaned Arabic."""
    if not raw:
        return None
    # Strip suffixes
    raw = re.sub(r'\s*(مترجم|مدبلج|كامل|اونلاين|وتحميل|HD|WEB-DL|1080p|BluRay)\s*$', '', raw).strip()
    raw = re.sub(r'\s*\d{4}\s*$', '', raw).strip()
    # Try to extract English title (Latin chars)
    eng = re.search(r'([A-Z][A-Za-z0-9\s\'\-:!?]+)', raw)
    if eng:
        candidate = eng.group(1).strip()
        if len(candidate) >= 2:
            return candidate
    # Fallback: return cleaned raw (remove leading "فيلم" etc.)
    raw = re.sub(r'^(فيلم\s+)+', '', raw).strip()
    return raw if raw else None

def extract_title(desc):
    if not desc:
        return None
    # Pattern: فيلم ... TITLE 2026
    m = re.search(r'فيلم\s+(?:ال[\w]+[\sو]*)*(.+?)\s+2026', desc)
    if m:
        raw = m.group(1).strip()
        raw = re.sub(r'\s*(مترجم|مدبلج|كامل|اونلاين|وتحميل)\s*$', '', raw)
        raw = re.sub(r'\s*\d{4}\s*$', '', raw)
        if raw:
            return raw
    m = re.search(r'فيلم\s+(?:ال[\w]+[\sو]*)*(.+?)\s+بجودة', desc)
    if m:
        raw = m.group(1).strip()
        raw = re.sub(r'\s*(مترجم|مدبلج|كامل|اونلاين)\s*$', '', raw)
        if raw:
            return raw
    m = re.search(r'\"(.+?)\"\s*\d{4}', desc)
    if m:
        return m.group(1).strip()
    # Patterns for "تنبيه" items
    m = re.search(r'من\s+فيلم\s+(.+?)(?:\s+\d{4}|$)', desc)
    if m:
        return m.group(1).strip()
    return None

# Known movies from web search
KNOWN_MOVIES = [
    # (desc_start, title_en, title_ar, tmdb_poster_path)
    ("مدينة ساحلية تتعرض لإعصار", "Thrash", "ثراش", "/adk8weka3O5648g3de4z3y4aE7G.jpg"),
    ("مخلوق غابة صغير", "Swapped", "سوابد", "/tHhxWxge06goXU6ZQH1hj7vK8Hd.jpg"),
    ('حول فتاة تُدعى "مايبل', "Hoppers", "هوبرز", "/xjtWQ2CL1mpmMNwuU5HeS4Iuwuu.jpg"),
]

changes = {"found_known": 0, "extracted_cleaned": 0, "not_found": 0, "total_cleaned": 0}

for item in items:
    title = (item.get("title", "") or "").strip()
    desc = (item.get("description", "") or "").strip()
    poster = item.get("poster", "") or ""
    
    new_title = None
    new_poster = None
    
    # 1. Check known descriptions first
    for prefix, en, ar, poster_path in KNOWN_MOVIES:
        if desc.startswith(prefix):
            new_title = en
            new_poster = f"https://image.tmdb.org/t/p/w500{poster_path}"
            changes["found_known"] += 1
            break
    
    if new_title is None:
        # 2. Try to extract from description
        extracted = extract_title(desc)
        if extracted:
            cleaned = clean_title(extracted)
            if cleaned:
                new_title = cleaned
                changes["extracted_cleaned"] += 1
            else:
                new_title = extracted
                changes["extracted_cleaned"] += 1
        else:
            changes["not_found"] += 1
    
    if new_title:
        item["title"] = new_title
    if new_poster:
        item["poster"] = new_poster

# Count results
title_counts = {}
for item in items:
    t = item.get("title", "") or ""
    title_counts[t] = title_counts.get(t, 0) + 1

with open(INPUT, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"Known movie assignments: {changes['found_known']}")
print(f"Extracted from desc + cleaned: {changes['extracted_cleaned']}")
print(f"Not found (still need manual): {changes['not_found']}")
print(f"\nTitle distribution:")
for t, c in sorted(title_counts.items(), key=lambda x: -x[1])[:20]:
    print(f"  {c:4d}x  {t[:50]}")
