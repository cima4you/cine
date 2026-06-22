# StreamIMDb Scraper

سكريبتات سكراب موقع streamimdb.ru لجلب 91,043 فيلم وتحويلها إلى بيانات JavaScript للموقع.

## السكريبتات الأساسية

### 1. `scrape_streamimdb.py` — السكراب الرئيسي (ثنائي المرحلة)

يجلب بيانات الأفلام على مرحلتين:

**المرحلة الأولى (Listings):** تجلب صفحات التصفح (`/movies?vaplayer_path=movies&page=N`).
- 2602 صفحة، كل صفحة 35 فيلم = 91,043 فيلم
- تستخرج: slug, title, year, poster, contentType
- تحفظ checkpoint كل 25 صفحة في `data/streamimdb_movies.json`
- تحفظ التقدم في `data/state.json`

**المرحلة الثانية (Embeds):** تزور صفحة كل فيلم (`/movie/{slug}`) لاستخراج الـ numeric embed ID.
- تستخرج `data-src="/embed/movie/{numeric_id}"` من صفحة التفاصيل
- تحفظ الرابط في `watch_server_url`
- الـ hash الموجود في الـ slug (مثل `nqox`) لا يشتغل كـ embed — لازم الرقم (مثل `1477317`)

#### الخيارات:

| الخيار | الوصف |
|--------|-------|
| `--listings-only` | تشغيل المرحلة الأولى فقط |
| `--embeds-only` | تشغيل المرحلة الثانية فقط |
| `--resume` | الاستمرار من آخر حفظ |
| `--fresh` | مسح الحالة والبدء من جديد |
| `--page-from N` | بدء التصفح من صفحة N |
| `--page-to N` | التوقف عند صفحة N |
| `--from N` | بدء معالجة embed من الفهرس N |
| `--to N` | التوقف عند الفهرس N |
| `--limit N` | عدد الصفحات القصوى للتصفح |

#### أمثلة التشغيل (PowerShell):

```powershell
# تشغيل المرحلة الأولى — صفحات 1-500
python screpte/streamimdb/scrape_streamimdb.py --listings-only --page-to 500

# استمرار التصفح (من آخر صفحة محفوظة)
python screpte/streamimdb/scrape_streamimdb.py --listings-only --resume

# تشغيل المرحلة الثانية — معالجة أول 150 فيلم
python screpte/streamimdb/scrape_streamimdb.py --embeds-only --resume --from 0 --to 150

# تشغيل المرحلة الثانية — كاملة
python screpte/streamimdb/scrape_streamimdb.py --embeds-only --resume

# تشغيل المرحلتين معاً
python screpte/streamimdb/scrape_streamimdb.py --resume

# عرض المساعدة
python screpte/streamimdb/scrape_streamimdb.py --help
```

ملاحظة: الـ state.json يدمج المفاتيح (`listings_page` + `embeds_index`) بدلاً من استبدالها، فلا تفقد التقدم عند التبديل بين المرحلتين.

### 2. `convert_to_js.py` — تحويل JSON إلى JS

يقرأ `data/streamimdb_movies.json` ويكتب `data-streamimdb.js` في جذر المشروع.

```powershell
python screpte/streamimdb/convert_to_js.py
```

الخرج يكون ملف JavaScript بالشكل:
```js
const cd_streamimdb = [
  {
    "title": "Your Fault: London",
    "year": "2026",
    "type": "StreamIMDb",
    "contentType": "movie",
    "poster": "https://image.tmdb.org/t/p/w342/...jpg",
    "servers": [
      {"name": "StreamIMDb", "url": "https://streamimdb.ru/embed/movie/1477317", "isDefault": true}
    ]
  },
  ...
];
```

إذا كان `watch_server_url` فارغاً، يبني رابط احتياطي من أول جزء من الـ slug (مثل `nqox`) — لكن هذه الروابط الاحتياطية قد لا تشتغل على nextgencloudfabric.com.

## هيكل الملفات

```
screpte/streamimdb/
├── scrape_streamimdb.py       # السكراب الرئيسي
├── convert_to_js.py           # التحويل إلى JS
├── README.md                  # هذا الملف
└── data/
    ├── streamimdb_movies.json # بيانات الأفلام الخام (JSON)
    ├── state.json             # حالة التقدم (listings_page + embeds_index)
    └── _check_*.py            # ملفات اختبار مؤقتة

(data-streamimdb.js في جذر المشروع)
├── data-streamimdb.js         # الأفلام بصيغة JS
├── data-loader.js             # يجمع كل cd_* في contentData
├── index.html                 # الموقع + CATEGORIES
└── logo.png                   # شعار الموقع
```

## سير العمل الكامل

1. **جلب التصفح:** `--listings-only --resume` (أو بـ `--page-from`/`--page-to`)
2. **جلب الـ embed IDs:** `--embeds-only --resume --from N --to M` (على دفعات)
3. **تحويل إلى JS:** `python convert_to_js.py`
4. **تحديث الموقع:** تضيف `cd_streamimdb` إلى `data-loader.js` وفئة إلى `CATEGORIES` في `index.html`

## ملاحظات مهمة

- **السرعة (مرحلة الـ embeds):** جلب متزامن (concurrent) بـ 5 threads — ~2500-3000 فيلم/دقيقة، ~30-40 دقيقة للتشغيل الكامل للـ 91,043 فيلم
- **`--parallel N`:** تتحكم بعدد الـ threads (الافتراضي 5). زد إلى 10 للسرعة القصوى
- **الترميز:** كل الملفات بـ UTF-8 (الأسماء العربية تتطلب `encoding='utf-8'`)
- **الـ embed ID:** الرقم فقط هو اللي يشتغل على nextgencloudfabric.com. الـ hash من الـ slug لا يشتغل ويعطي 404
- **الـ Referer:** nextgencloudfabric.com يتطلب `Referer: streamimdb.ru` (الـ iframe يرسله تلقائياً)
