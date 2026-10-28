<!-- BANNER START -->
<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=32&duration=2800&pause=2000&color=A020F0&center=true&vCenter=true&width=600&lines=Neshan+Maps+Scraper;Interactive+Map+Selector;Extract+Places+Like+a+Pro" alt="Typing SVG" />
</p>

<p align="center">
  <b>📍 A powerful, colourful, and stealthy scraper for Neshan Maps</b><br>
  <i>Interactive map box selector, live query counting, full photo downloading & place approval</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License"/>
  <img src="https://img.shields.io/badge/Playwright-Powered-orange?logo=playwright" alt="Playwright"/>
  <img src="https://img.shields.io/badge/Interactive-Map_Selector-purple" alt="Interactive Map"/>
</p>

<pre align="center">
███╗   ██╗███████╗███████╗██╗  ██╗ █████╗ ███╗   ██╗
████╗  ██║██╔════╝██╔════╝██║  ██║██╔══██╗████╗  ██║
██╔██╗ ██║█████╗  ███████╗███████║███████║██╔██╗ ██║
██║╚██╗██║██╔══╝  ╚════██║██╔══██║██╔══██║██║╚██╗██║
██║ ╚████║███████╗███████║██║  ██║██║  ██║██║ ╚████║
╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
</pre>

---

## ✨ ویژگی‌های جدید و کلیدی (Key Features)

- 🎯 **حالت تعاملی و انتخاب محدوده روی نقشه (Interactive Map Selector)**:
  - با اجرای برنامه، مرورگر باز شده و یک پنل کنترلی مدرن و شکیل روی سایت نشان ظاهر می‌شود.
  - می‌توانید با کلیک روی دکمه **«رسم مربع روی نقشه»**، یک کادر دلخواه روی نقشه بیندازید یا با ماوس درگ کنید.
- 🔢 **شمارش زنده تعداد نتایج (Live Query Counting)**:
  - قبل از اسکرپ، دکمه **«شمارش نتایج»** را می‌زنید و دقیقاً متوجه می‌شوید چند مورد (مثلاً آرایشگاه، کافه و...) در آن کادر وجود دارد.
- ✋ **تایید مرحله‌به‌مرحله با امکان رد کردن (Step-by-Step Approval & Skip)**:
  - قبل از استخراج هر مکان، یک پاپ‌آپ با پیش‌نمایش نام و آدرس ظاهر می‌شود و می‌توانید آن را **تایید**، **رد (Skip)**، **استخراج خودکار همه** یا **توقف و ذخیره** کنید.
- 🖼️ **دانلود کامل تصاویر و عکس‌ها (Full Photo Downloader)**:
  - دانلود تمام عکس‌های باکیفیت هر مکان در پوشه اختصاصی (`downloads/<query>/...`).
- 📌 **استخراج کامل‌ترین داده‌ها**:
  - نام، دسته‌بندی، آدرس، شماره تماس، وب‌سایت، ساعت کاری امروز، امتیاز، تعداد نظرات، **مختصات جغرافیایی (Latitude & Longitude)**، لینک مستقیم در نشان، و توضیحات مکان.
- 📁 **خروجی با فرمت‌های گوناگون**: CSV (با پشتیبانی کامل اکسل و UTF-8-BOM)، JSON، Parquet، و SQLite.

---

## 🚀 نصب و راه‌اندازی (Installation)

```bash
# کلون کردن پروژه
git clone https://github.com/your-username/neshan-scraper.git
cd neshan-scraper

# نصب وابستگی‌ها
pip install -r requirements.txt

# نصب مرورگر پلی‌رایت (در صورت نیاز - روی ویندوز به صورت خودکار کروم پیش‌فرض استفاده می‌شود)
playwright install chromium
```

---

## 🖥️ نحوه استفاده (Usage)

### ۱. اجرای حالت تعاملی (پیشنهادی):
کافیست اسکریپت را بدون هیچ آرگومانی اجرا کنید (یا با فلگ `-i`):

```bash
python neshan_scraper.py
```
یا:
```bash
python neshan_scraper.py -i
```

1. سایت نشان در مرورگر باز می‌شود و پنل دستیار در گوشه صفحه ظاهر می‌شود.
2. روی دکمه **«انتخاب محدوده (رسم مربع روی نقشه)»** کلیک کنید و روی نقشه مربع دلخواه را بکشید.
3. دکمه **«شمارش نتایج در این محدوده»** را بزنید تا تعداد مکان‌ها محاسبه شود.
4. روی **«شروع استخراج اطلاعات (اسکرپ)»** کلیک کنید!

---

### ۲. اجرای حالت خط فرمانی خودکار (CLI Mode):

```bash
python neshan_scraper.py -s "آرایشگاه تهران" -t 20 -f csv --download-photos
```

برای اجازه گرفتن قبل از استخراج هر مکان در کنسول:
```bash
python neshan_scraper.py -s "کافه شیراز" -t 15 --ask-confirm --download-photos
```

---

### ⚡ تمام سوئیچ‌ها و آرگومان‌ها (All Arguments)

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--interactive` | `-i` | اجرای حالت تعاملی و رسم مربع روی نقشه نشان | `True` (در صورت عدم ارسال کوئری) |
| `--search` | `-s` | کلمه جستجو در حالت CLI | `""` |
| `--total` | `-t` | حداکثر تعداد مکان‌ها برای استخراج | `5` |
| `--ask-confirm` | | اجازه گرفتن قبل از اسکرپ هر مکان (امکان رد/Skip) | `False` (در UI تیک دارد) |
| `--download-photos`| | دانلود تمام تصاویر و عکس‌های هر مکان | `False` (در UI تیک دارد) |
| `--output` | `-o` | نام پایه فایل خروجی | `neshan_export` |
| `--format` | `-f` | فرمت خروجی: `csv`, `json`, `parquet`, `sqlite` | `csv` |
| `--headless` | | اجرای بدون محیط گرافیکی (مخصوص سرور/CLI) | `False` |
| `--delay` | | تنظیم وقفه جهت جلوگیری از بلاک: `low`, `medium`, `high` | `medium` |
| `--log` | | سطح لاگ: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

---

## 📦 نمونه ساختار خروجی (CSV / JSON)

| name | category | address | phone_number | website | opening_hours_today | rating | reviews_count | latitude | longitude | photo_count | photo_paths |
|------|----------|---------|--------------|---------|---------------------|--------|---------------|----------|-----------|-------------|-------------|
| سالن زیبایی دنیا | سالن آرایش | تهران، بزرگراه ستاری... | ۰۹۱۲۰۵۸۰۷۷۲ | https://... | ۱۰:۰۰ - ۱۹:۰۰ | 4.5 | 38 | 35.710 | 51.491 | 3 | downloads/.../photo_1.jpg |

---

## ⚠️ سلب مسئولیت (Disclaimer)

این ابزار صرفاً با اهداف پژوهشی و آموزشی توسعه یافته است. لطفاً به قوانین سرویس‌دهی وب‌سایت احترام گذاشته و از ارسال درخواست‌های سنگین و غیرمتعارف خودداری فرمایید.

---

## 📄 لایسنس

MIT © EhsanShahbazi
