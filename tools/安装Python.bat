@echo off
chcp 936 >nul
title ÔÆÖÇÊµÑµÖúÊÖ - Python °²×°³ÌĞò
cd /d "%~dp0.."

echo [95m==============================================[0m
echo [95m     ÔÆÖÇÊµÑµÖúÊÖ - Python °²×°³ÌĞò[0m
echo [95m==============================================[0m
echo.
python --version >nul 2>&1
if errorlevel 1 goto need_install
python --version
echo  Python ÒÑ°²×°,ÎŞĞèÖØ¸´°²×°
echo  Ë«»÷¸ùÄ¿Â¼ [Ò»¼üÔËĞĞ.bat] ¼´¿ÉÊ¹ÓÃ

echo.
pause
exit /b

:need_install
echo  Î´¼ì²âµ½ Python,¿ªÊ¼×Ô¶¯°²×°...
where winget >nul 2>&1
if errorlevel 1 goto use_curl
winget install Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements
if not errorlevel 1 goto refresh

:use_curl
set "PYEXE=%TEMP%\yunzhi_py\python-3.11.9-amd64.exe"
if not exist "%TEMP%\yunzhi_py" mkdir "%TEMP%\yunzhi_py"
curl -L -o "%PYEXE%" "https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-amd64.exe" --connect-timeout 30
if exist "%PYEXE%" goto install
curl -L -o "%PYEXE%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" --connect-timeout 30
if exist "%PYEXE%" goto install
echo  ÏÂÔØÊ§°Ü,ÇëÊÖ¶¯°²×°: https://www.python.org/downloads/
echo  Îñ±Ø¹´Ñ¡ Add Python to PATH

echo.
pause
exit /b

:install
if exist "%PYEXE%" "%PYEXE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

:refresh
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
python --version >nul 2>&1
if errorlevel 1 goto path_warn
python --version
echo  °²×°³É¹¦! Ë«»÷¸ùÄ¿Â¼ [Ò»¼üÔËĞĞ.bat] ¼´¿ÉÊ¹ÓÃ

echo.
pause
exit /b

:path_warn
echo  ÒÑ°²×°µ«µ±Ç°´°¿ÚÎ´Ê¶±ğ,Çë¹Ø±Õ´°¿ÚºóÖØĞÂË«»÷±¾ÎÄ¼ş

echo.
pause
exit /b
