import re, json

# Read data-arabic.js
with open('data/data-arabic.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Parse the array
match = re.search(r'const cd_arabic = \[(.*)\];', content, re.DOTALL)
array_text = '[' + match.group(1) + ']'
arabic_data = json.loads(array_text)
print(f'Before: {len(arabic_data)} movies')

# Titles to remove (the 35 from the comparison)
to_remove = {
    '6 ايام 2025', 'البحث عن منفذ لخروج السيد رامبو 2024',
    'سيكو سيكو', 'ع الزيرو 2023', 'عادل مش عادل 2024',
    'فيلم 19 ب', 'فيلم 6 ايام', 'فيلم إتنين للإيجار',
    'فيلم الحريفة 2 الريمونتادا', 'فيلم الدعوة عامة',
    'فيلم الرجل الرابع', 'فيلم السنيور', 'فيلم العنكبوت',
    'فيلم الفستان الأبيض 2024', 'فيلم اللعب مع العيال',
    'فيلم بحبك', 'فيلم برا المنهج', 'فيلم تحت تهديد السلاح',
    'فيلم تسليم أهالي', 'فيلم حدث في 2 طلعت حرب',
    'فيلم حظك اليوم', 'فيلم خرجوا ولم يعودوا',
    'فيلم خطة مازنجر', 'فيلم زومبي', 'فيلم شلبي',
    'فيلم طرف تالت', 'فيلم عمهم', 'فيلم فارس',
    'فيلم فضل ونعمة', 'فيلم كيرة والجن',
    'فيلم نبيل الجميل أخصائي تجميل', 'فيلم نزوح',
    'فيلم هاشتاج جوزني', 'فيلم ولا غلطة', 'معالي ماما',
}

filtered = [m for m in arabic_data if m.get('title', '').strip() not in to_remove]
removed = len(arabic_data) - len(filtered)
print(f'Removed: {removed}, After: {len(filtered)} movies')

# Build comment with count
comment = f'// أفلام عربية — {len(filtered)} عنصر'

# Compact single-line format (matching original style)
array_str = json.dumps(filtered, ensure_ascii=False)
js_content = f'{comment}\nconst cd_arabic = {array_str};'

with open('data/data-arabic.js', 'w', encoding='utf-8') as f:
    f.write(js_content)

print('Done! data-arabic.js updated.')
