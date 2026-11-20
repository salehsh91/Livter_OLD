# یادداشت‌های پورت Android

## تفاوت DLL و SO
`cppmain.dll` و `SDL3.dll` داخل ZIP اصلی، فایل‌های Windows هستند. برای Android
باید با Android NDK دوباره از سورس ساخته شوند؛ تغییر پسوند DLL به SO کار نمی‌کند.

## وابستگی SDL3
`CMakeLists.txt` نسخه‌های SDL3 و SDL3_image را از سورس رسمی دریافت می‌کند:
- SDL3 3.4.14
- SDL3_image 3.4.8

این نسخه‌ها با نسخهٔ headerهای موجود در ZIP اصلی هم‌نسخه‌اند.

## مرحلهٔ بعد برای APK کامل
برای اجرای همان بازی فعلی باید این موارد انجام شود:
1. وارد کردن Android project رسمی SDL3 و SDLActivity/JNI آن.
2. فراهم کردن Python runtime سازگار با Android.
3. تغییر بارگذاری `cppfuncs.py` از `cppmain.dll` به کتابخانهٔ native اندروید.
4. اطمینان از اینکه SDL3 فقط از مسیر Activity اندروید initialize شود و Python
   game loop در thread/lifecycle درست اجرا شود.
5. جایگزینی ورودی صفحه‌کلید فعلی با ورودی لمسی؛ `contoroler.py` فعلاً فقط
   scancodeهای صفحه‌کلید را می‌خواند.

## چرا buildozer.spec فعلی کافی نیست؟
`buildozer.spec` در ZIP اصلی مربوط به مسیر Pygame/SDL2 است. این پروژهٔ فعلی از
SDL3/C++ و ctypes استفاده می‌کند؛ بنابراین Buildozer با همان تنظیمات، DLL
ویندوزی را به کتابخانهٔ Android تبدیل نمی‌کند.
