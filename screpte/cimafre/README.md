# Cimafre Scraper — سكراب cimafre.site

سكريبتات سكراب موقع cimafre.site لجلب الأفلام العربية مع جميع سيرفرات المشاهدة وتحويلها إلى بيانات JavaScript للموقع.

## السكريبتات الأساسية

### 1. `scrape_cimafre.py` — السكراب الرئيسي

يجلب الأفلام العربية من cimafre.site على مرحلتين:

**المرحلة الأولى (Listings):** تجلب صفحات التصفح (`category.php?cat=arabic-moives&page=N`).
- يستخرج: vid (hash), عنوان, صورة مصغرة, المدة
- يحفظ في `data/arabic_movies.json`
- التصنيف الحالي: `arabic-moives` (أفلام عربية)
- كل صفحة تحتوي على ~24 فيلم

**المرحلة الثانية (Servers):** تزور `play.php?vid={vid}` لاستخراج جميع سيرفرات المشاهدة.
- تستخرج قائمة `<ul class="WatchList">` — 11 سيرفر لكل فيلم
- السيرفرات: Cimaf، Vk/Vkvideo، Vidspeed، Larhu، Emturbovid، Luluvid، Uqload، Vikingfile/Minochinos، Dsvplay، Ok، Voe
- السيرفر الأساسي (Cimaf) يحتوي على رابط M3U8 من hd.cimaf.xyz/albaplayer

#### الخيارات:

| الخيار | الوصف |
|--------|-------|
| `--from N` | بدء التصفح من صفحة N |
| `--to N` | التوقف عند صفحة N |
| `--servers` | تشغيل مرحلة جلب السيرفرات فقط |
| `--parallel N` | عدد الطلبات المتزامنة لجلب السيرفرات (الافتراضي 5) |

#### أمثلة التشغيل (PowerShell):

```powershell
# تشغيل مرحلتي التصفح وجلب السيرفرات معاً — صفحات 1-50
python screpte/cimafre/scrape_cimafre.py --to 50 --parallel 10

# تشغيل التصفح فقط — صفحات 20-40
python screpte/cimafre/scrape_cimafre.py --from 20 --to 40

# جلب السيرفرات للأفلام الموجودة فقط (بدون تصفح)
python screpte/cimafre/scrape_cimafre.py --servers --parallel 10
```

ملاحظة: `--from` يتجاوز `processed_idx` في الـ state. التصفح يضيف أفلام جديدة للموجودين بدون مسح القديم.

### 2. `convert_to_js.py` — تحويل JSON إلى JS

يقرأ `data/arabic_movies.json` ويكتب `data/data-cimafre.js` و `data/data-cimafre.json`.

```powershell
python screpte/cimafre/convert_to_js.py
```

الخرج يكون ملف JavaScript بالشكل:
```js
const cd_cimafre = [
  {
    id: "19997b01f",
    title: "الكلام على ايه : اول ليلة 2026",
    servers: [
      {"id": 1, "name": "Cimaf", "url": "https://hd.cimaf.xyz/albaplayer/el-kalam-ala-eh/"},
      {"id": 2, "name": "Vk", "url": "https://vk.com/video_ext.php?oid=...&id=...&hash=1"},
      {"id": 3, "name": "Vidspeed", "url": "https://vidspeed.org/embed-....html"},
      ...
    ],
    poster: "https://cumafree.onl/uploads/thumbs/....jpg",
    duration: "1:47:42",
    type: "عربي",
    contentType: "movie"
  },
  ...
];
```

## هيكل الملفات

```
screpte/cimafre/
├── scrape_cimafre.py       # السكراب الرئيسي
├── convert_to_js.py        # التحويل إلى JS/JSON
├── README.md               # هذا الملف
├── data/
│   └── arabic_movies.json  # بيانات الأفلام الخام (JSON)
│
└── *_test / check_*.py     # ملفات اختبار وتجريب

data/
├── data-cimafre.js         # الأفلام بصيغة JS
├── data-cimafre.json       # الأفلام بصيغة JSON (للمراجعة)
├── data-loader.js          # يجمع كل cd_* في contentData
└── index.html              # الموقع + CATEGORIES
```

## سير العمل الكامل

1. **جلب التصفح:** `python scrape_cimafre.py --to 999` (أو العدد المطلوب من الصفحات)
2. **جلب السيرفرات:** `python scrape_cimafre.py --servers --parallel 10`
3. **تحويل إلى JS:** `python convert_to_js.py`
4. **تحديث الموقع:** أضف `<script src="data-cimafre.js">` إلى `index.html` و `cd_cimafre` إلى `data-loader.js`

## ملاحظات مهمة

- **مشكلة Cloudflare:** الصفحات الرئيسية (`category.php`, `watch.php`) محمية بـ Cloudflare Bot Management. السيرفرات تُحجب من الـ HTML. **الحل:** استخدام `play.php?vid={vid}` — Cloudflare لا يحجب هذه الصفحة وتحتوي على WatchList كاملة
- **سيرفر واحد فقط:** إذا لم تجد الـ WatchList، جرب `embed.php?vid={vid}` الذي يعطي رابط السيرفر الأساسي (Cimaf) فقط
- **السرعة (مرحلة السيرفرات):** جلب متزامن بـ 10 threads — ~25-30 فيلم/دقيقة
- **الترميز:** كل الملفات بـ UTF-8
- **سيرفر Larhu:** هو الأسرع والأكثر استقراراً (مرتب أولاً في `sortServers`)
- **روابط التحميل:** بعض الأفلام تحتوي على `downloadServers` — تُستخرج تلقائياً من `play.php`
- **المودال في الموقع:** يدعم `servers[]` مع `name` و `url` — أزرار السيرفرات تعمل تلقائياً بدون تعديل
