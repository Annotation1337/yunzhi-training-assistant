@echo off
chcp 936 >nul
title ÔÆÖÇÊµÑµÖúÊÖ - °²×° OCR ½ØÍ¼Ê¶±ğÒÀÀµ
cd /d %~dp0

echo [95m==============================================[0m
echo [95m     ÔÆÖÇÊµÑµÖúÊÖ - °²×° OCR ½ØÍ¼Ê¶±ğÒÀÀµ[0m
echo [95m==============================================[0m
echo.
echo  ÓÃÍ¾: ÅÅ´íÕï¶ÏÒ³ÃæµÄ¡¸½ØÍ¼Ê¶±ğ¡¹¹¦ÄÜ
echo  ËµÃ÷: ±¾½Å±¾Ö»×° Python °ü pytesseract;
echo        Tesseract ³ÌĞò±¾ÌåĞèÁíĞĞÏÂÔØ(Ô¼ 60MB)
echo  Ô¤¼ÆºÄÊ±: Ô¼ 10-30 Ãë
echo.
echo  µÚ 1 ²½: ¼ì²â Python
python --version >nul 2>&1
if errorlevel 1 goto od_no_py
python --version
echo.
echo  µÚ 2 ²½: °²×° pytesseract (Çå»ªÔ´)
python -m pip install pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 python -m pip install pytesseract
echo.
echo  µÚ 3 ²½: ÑéÖ¤
python -c "import pytesseract; print('  pytesseract:', pytesseract.__version__)"
if errorlevel 1 goto od_fail
echo.
echo  ==============================================
echo   pytesseract ×°ºÃÁË!
echo  ==============================================
echo  ÏÂÒ»²½:
echo    1. ×° Tesseract ³ÌĞò±¾Ìå (Windows ÓÃ»§):
echo       https://github.com/UB-Mannheim/tesseract/wiki
echo       ÏÂÔØ tesseract-ocr-w64-setup-xxx.exe °²×°
echo       °²×°Ê±¹´Ñ¡¡¸¼òÌåÖĞÎÄ¡¹ÓïÑÔ°ü
echo    2. »òÓÃ winget Ò»ĞĞÃüÁî:
echo       winget install tesseract-ocr.tesseract
echo    3. ÖØÆô ÔÆÖÇ ºó,ÅÅ´íÕï¶ÏÒ³ÃæµÄ½ØÍ¼Ê¶±ğ¼´¿ÉÉúĞ§
echo.
echo  Èç¹û²»×° Tesseract ³ÌĞò,ÔÆÖÇÆäËû¹¦ÄÜ(ÖªÊ¶¿â/ÁªÍø/»­ÍØÆËÍ¼)ÍêÈ«Õı³£
goto od_end

:od_no_py
echo  ´íÎó: Î´¼ì²âµ½ Python,ÇëÏÈÔËĞĞ tools\°²×°Python.bat
goto od_end

:od_fail
echo  ´íÎó: pytesseract °²×°Ê§°Ü,Çë¼ì²éÍøÂçºóÖØÊÔ
echo  ÊÖ¶¯ÃüÁî:
echo    python -m pip install pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple

:od_end

echo.
pause
exit /b
