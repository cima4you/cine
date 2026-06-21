# OOAnime Scraper — سكراب ooanime.com

سكريبت سكراب موقع ooanime.com لجلب مسلسلات الكرتون القديمة (كرتون الزمن الجميل) مع جميع الحلقات وروابط MP4 وتحويلها إلى JavaScript.

## السكريبتات الأساسية

### 1. `scrape_ooanime.py` — السكراب الرئيسي (ثلاثي المرحلة)

يجلب بيانات المسلسلات على 3 مراحل:

**المرحلة الأولى (Series List):** تجلب قائمة المسلسلات من `/?s=series_list`.
- 180 مسلسل (IDs 36–227)
- يستخرج: id, title, poster, description, year, rating, quality

**المرحلة الثانية (Detail):** تزور صفحة كل مسلسل (`/?s=series_detail&id={id}`).
- يستخرج: كود JavaScript المضمن الذي يحتوي على بيانات المواسم والحلقات
- يحفظ في بنية `seasons[]` داخل كل مسلسل

**المرحلة الثالثة (Episodes):** تزور صفحة كل حلقة لاستخراج رابط الفيديو MP4.
- رابط MP4 المباشر: `https://new.ooanime.com/OOAnime.com/{SeriesName}.S{season}E{ep}.mp4`
- ملاحظة: بعض الحلقات قد لا تحتوي على رابط فيديو (محتوى محذوف)

#### الخيارات:

| الخيار | الوصف |
|--------|-------|
| `--series-only` | تشغيل المرحلة الأولى فقط |
| `--detail-only` | تشغيل المرحلة الثانية فقط |
| `--episodes-only` | تشغيل المرحلة الثالثة فقط |
| `--resume` | الاستمرار من آخر حفظ |
| `--fresh` | مسح الحالة والبدء من جديد |
| `--from N` | بدء معالجة المسلسلات من الفهرس N |
| `--to N` | التوقف عند الفهرس N |
| `--parallel N` | عدد الطلبات المتزامنة (الافتراضي 5) |
| `--help` | عرض المساعدة |

#### أمثلة التشغيل (PowerShell):

```powershell
# تشغيل المرحلة الأولى — قائمة المسلسلات
python screpte/ooanime/scrape_ooanime.py --series-only

# تشغيل المرحلة الثانية — تفاصيل المسلسلات (أول 20)
python screpte/ooanime/scrape_ooanime.py --detail-only --from 0 --to 20

# تشغيل المرحلة الثانية — كاملة
python screpte/ooanime/scrape_ooanime.py --detail-only --resume

# تشغيل المرحلة الثالثة — روابط الحلقات
python screpte/ooanime/scrape_ooanime.py --episodes-only --resume

# تشغيل المرحلتين الثانية والثالثة معاً
python screpte/ooanime/scrape_ooanime.py --detail-only --resume && python screpte/ooanime/scrape_ooanime.py --episodes-only --resume
```

### 2. `convert_to_js.py` — تحويل JSON إلى JS

يقرأ `data/ooanime_series.json` ويكتب `data/data-ooanime.js` و `data/data-ooanime.json`.

```powershell
python screpte/ooanime/convert_to_js.py
```

ميزات المحول:
- يستخرج رقم الحلقة من الرابط (`Ep\d+`) ومن العنوان (`الحلقة_\d+`)
- يرتب الحلقات تصاعدياً حسب الرقم
- يضيف `seasonNumber` متسلسل (1, 2, 3...) بدلاً من ID من قاعدة البيانات
- يصدر JSON للتفحص و JS للتشغيل

الخرج يكون ملف JavaScript بالشكل:
```js
const cd_ooanime = [
  {
    title: "السندباد بحري",
    poster: "https://cdn.ooanime.com/...jpg",
    year: "2025",
    rating: "5.0",
    seasonNumber: 1,
    type: "كرتون",
    contentType: "series",
    episodes: [
      {
        episodeNumber: 1,
        title: "الحلقة 1",
        videoUrl: "https://new.ooanime.com/OOAnime.com/Sindbad.S1E1.mp4",
        servers: [{"name": "mp4", "url": "https://new.ooanime.com/OOAnime.com/Sindbad.S1E1.mp4"}]
      },
      ...
    ]
  },
  ...
];
```

## هيكل الملفات

```
screpte/ooanime/
├── scrape_ooanime.py       # السكراب الرئيسي (3 مراحل)
├── convert_to_js.py        # التحويل إلى JS/JSON
├── README.md               # هذا الملف
├── data/
│   └── ooanime_series.json # بيانات المسلسلات الخام (JSON)
│
└── _check_*.py / _explore.py  # ملفات اختبار وتجريب

data/
├── data-ooanime.js         # المسلسلات بصيغة JS
├── data-ooanime.json       # المسلسلات بصيغة JSON (للمراجعة)
├── data-loader.js          # يجمع كل cd_* في contentData
└── index.html              # الموقع + CATEGORIES
```

## سير العمل الكامل

1. **قائمة المسلسلات:** `--series-only`
2. **تفاصيل المسلسلات:** `--detail-only --resume`
3. **روابط الحلقات:** `--episodes-only --resume`
4. **تحويل إلى JS:** `python convert_to_js.py`
5. **تحديث الموقع:** أضف `<script src="data-ooanime.js">` إلى `index.html` و `cd_ooanime` إلى `data-loader.js`

## ملاحظات مهمة

- **السرعة (مرحلة الحلقات):** جلب متزامن بـ 5 threads. المسلسل الواحد يستغرق ~2-3 ثانية. إجمالي 7,105 حلقة
- **روابط MP4:** مباشرة من new.ooanime.com — لا تحتاج هيدرات خاصة. يمكن تشغيلها مباشرة في `<video>`
- **معدل النجاح:** 97.8% من الحلقات تحتوي على روابط فيديو (6,948 من 7,105)
- **الترميز:** كل الملفات بـ UTF-8
- **Episode Pagination:** المودال يعرض 10 حلقات لكل صفحة مع أزرار ‹ ›
- **المودال في الموقع:** يدعم المواسم (`seasonSelector`) والحلقات (`episodeSelector`) والسيرفرات (`servers[]` لكل حلقة)
