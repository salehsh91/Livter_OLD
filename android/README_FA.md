# بستهٔ آماده‌سازی اندروید Livter

این ZIP از فایل واقعی `Game(1).zip` ساخته شده و سورس فعال Python/C++ و پوشهٔ
`assets` را نگه می‌دارد. فایل‌های DLL ویندوزی، فایل‌های `.exe`، پوشهٔ `.git`
و cacheها عمداً وارد نشده‌اند؛ این فایل‌ها برای APK قابل استفاده نیستند.

## وضعیت فعلی: بستهٔ آماده‌سازی، نه APK نهایی

کد فعلی Livter دو بخش دارد:
- منطق بازی در Python؛
- رندر و ورودی SDL3 در `cmain.cpp` که Python از طریق `ctypes` فراخوانی می‌کند.

در سورس فعلی `cppfuncs.py` نام `cppmain.dll` را بارگذاری می‌کند. DLL ویندوزی
روی Android اجرا نمی‌شود و باید با NDK به یک کتابخانهٔ `.so` ساخته شود.
همچنین SDL3 در Android به Activity/JNI مخصوص خودش نیاز دارد. طبق راهنمای
رسمی SDL3، پروژه باید در قالب Android Gradle project ساخته شود و SDL3 نیز
برای ABI اندروید کامپایل شود.

**مانع اصلی که هنوز حل نشده:** این ZIP در خودش runtime اندرویدی Python ندارد
و اتصال Python به SDL3 Android Activity هم هنوز پیاده‌سازی نشده است. بنابراین
فایل‌های این بسته را نباید به‌عنوان پروژه‌ای معرفی کرد که همین حالا APK کامل
Livter تولید می‌کند. ساختن صرفِ `liblivter_native.so` کافی نیست؛ چون حلقهٔ بازی
و منطق فعلی هنوز در Python اجرا می‌شوند.

## فایل‌های این بسته

- `Livter/`: سورس فعلی پروژه و assetها.
- `android/CMakeLists.txt`: پیکربندی اولیهٔ NDK برای ساخت کد C++ با SDL3 و
  SDL3_image.
- `android/cmain_android.cpp`: نسخهٔ سازگارشدهٔ ماکروی export برای Windows و
  Android.
- `android/PORTING_NOTES.md`: تغییرات لازم برای تکمیل اجرای Python روی Android.

## پیش‌نیازهای ساخت native

- Android SDK Platform 35 یا جدیدتر
- Android NDK r28c یا جدیدتر
- CMake
- JDK سازگار با Gradle

ABI پیش‌فرض `arm64-v8a` است که برای گوشی‌های ۶۴ بیتی مناسب است.
