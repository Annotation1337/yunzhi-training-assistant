@echo off
chcp 936 >nul
title ÔÆÖÇÊµÑµÖúÊÖ - ºó¶ËÆô¶¯³ÌĞò
cd /d "%~dp0.."

echo [95m==============================================[0m
echo [95m     ÔÆÖÇÊµÑµÖúÊÖ - ºó¶ËÆô¶¯³ÌĞò[0m
echo [95m==============================================[0m
echo.
echo  [±¾½Å±¾Î»ÓÚ tools Ä¿Â¼] ÆÕÍ¨ÓÃ»§ÈÕ³£Ö»ĞèË«»÷¸ùÄ¿Â¼ Ò»¼üÔËĞĞ.bat
echo.

echo  µÚ 1 ²½: ¼ì²é Python »·¾³
python --version >nul 2>&1
if errorlevel 1 goto so_no_python
python --version

echo  µÚ 2 ²½: ¼ì²é»ù´¡ÒÀÀµ (flask / Pillow / bs4 / matplotlib)
python -c "import flask" >nul 2>&1
if errorlevel 1 goto so_install_deps
python -c "import PIL" >nul 2>&1
if errorlevel 1 goto so_install_deps
python -c "import bs4" >nul 2>&1
if errorlevel 1 goto so_install_deps
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 goto so_install_deps
echo  ÒÀÀµÒÑ¾ÍĞ÷
goto so_check_ollama

:so_install_deps
echo  ÕıÔÚ°²×°»ù´¡ÒÀÀµ (²»º¬ PyTorch,Ô¼ 40MB)...
python -m pip install flask Pillow beautifulsoup4 matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 python -m pip install flask Pillow beautifulsoup4 matplotlib
python -c "import flask" >nul 2>&1
if errorlevel 1 goto so_install_fail
echo  ÒÀÀµ°²×°³É¹¦

:so_check_ollama
echo.
echo  µÚ 3 ²½: ¼ì²é±¾µØ´óÄ£ĞÍ Ollama (¿ÉÑ¡)
echo  ËµÃ÷: Ollama Îª¿ÉÑ¡Ïî,Î´°²×°Ò²²»Ó°ÏìÖªÊ¶¿âÎÊ´ğ
curl -s --max-time 2 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto so_no_ollama
echo  Ollama ÒÑÔÚÏß,ÖÇÄÜÎÊ´ğ½«ÆôÓÃ±¾µØ´óÄ£ĞÍÔöÇ¿
goto so_start_server

:so_no_ollama
echo  Î´¼ì²âµ½ Ollama,½«Ê¹ÓÃ ÖªÊ¶¿â+ÁªÍø¶µµ× Ä£Ê½
echo  ÈçĞèÆôÓÃ´óÄ£ĞÍ,ÇëÏÈ°²×° Ollama ²¢ÔËĞĞ ollama serve

:so_start_server
echo.
echo  µÚ 4 ²½: Æô¶¯ºó¶Ë·şÎñ
echo  ÇëÉÔºò,ä¯ÀÀÆ÷»á×Ô¶¯´ò¿ªÒ³Ãæ
echo  µØÖ·: http://localhost:5000
echo  ¹Ø±Õ±¾´°¿Ú¼´¿ÉÍ£Ö¹·şÎñ
echo.
python app.py
echo.
echo  ·şÎñÒÑÍ£Ö¹¡£
goto so_end

:so_no_python
echo  ´íÎó: Î´¼ì²âµ½ Python
echo  ÇëÏÈÔËĞĞ tools\°²×°Python.bat,»ò·ÃÎÊ https://www.python.org/downloads/ ÊÖ¶¯°²×°
echo  °²×°Ê±Îñ±Ø¹´Ñ¡ Add Python to PATH
goto so_end

:so_install_fail
echo  ´íÎó: ÒÀÀµ°²×°Ê§°Ü,Çë¼ì²éÍøÂçºóÖØÊÔ
echo  »òÊÖ¶¯ÔËĞĞ: python -m pip install flask Pillow beautifulsoup4 matplotlib

:so_end

echo.
pause
exit /b
