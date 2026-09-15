@echo off
chcp 936 >nul
title ÔÆÖÇÊµÑµÖúÊÖ - °²×° Ollama ±¾µØ´óÄ£ĞÍ·şÎñ
cd /d "%~dp0.."

echo [95m==============================================[0m
echo [95m     ÔÆÖÇÊµÑµÖúÊÖ - °²×° Ollama ±¾µØ´óÄ£ĞÍ·şÎñ[0m
echo [95m==============================================[0m
echo.
echo  Ê×´Î°²×°Ô¼Ğè 5-10 ·ÖÖÓ [ÏÂÔØÔ¼ 200MB]
echo  ÊÊÓÃÓÚ Windows 10 / 11 x64
echo  ÏÂÔØÔ´: ollama.com Ô­°æ [Ö±½ÓÏÂÔØ]
echo  ÈôÊ§°Ü: ³¢ÊÔ PowerShell, ÔÙÊ§°ÜÔòÌáÊ¾ÊÖ¶¯ÏÂÔØ
echo.

echo  µÚ 1 ²½: ¼ì²é Ollama ÊÇ·ñÒÑ°²×°
where ollama >nul 2>&1
if not errorlevel 1 goto already_installed

echo  µÚ 2 ²½: ÏÂÔØ Ollama °²×°°ü [À´Ô´ ollama.com Ô­°æ]
echo  ÏÂÔØÖĞ,ÇëÉÔºò...
echo.
if exist ollama-installer.exe goto skip_download

curl -L --retry 3 --retry-delay 5 -C - -o ollama-installer.exe --connect-timeout 15 --max-time 3600 https://ollama.com/download/OllamaSetup.exe
if not errorlevel 1 goto skip_download
echo  curl Ê§°Ü,³¢ÊÔ PowerShell...
del ollama-installer.exe >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command try { Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'ollama-installer.exe' -UseBasicParsing } catch { exit 1 }
if not errorlevel 1 goto skip_download
del ollama-installer.exe >nul 2>&1
goto download_fail

:skip_download
if not exist ollama-installer.exe goto download_fail
echo  ÏÂÔØÍê³É
echo.

echo  µÚ 3 ²½: ¾²Ä¬°²×° Ollama
echo  ÕıÔÚ°²×°,ÇëÉÔºò,¿ÉÄÜµ¯³ö UAC È·ÈÏ...
ollama-installer.exe /S
if errorlevel 1 goto install_fail
echo  °²×°Íê³É
echo.
del ollama-installer.exe >nul 2>&1

echo  µÚ 4 ²½: Æô¶¯ Ollama ·şÎñ
echo  Ollama °²×°ºó»á×Ô¶¯ºóÌ¨ÔËĞĞ,ÎŞĞèÊÖ¶¯Æô¶¯
echo  ÈçÎ´Æô¶¯,ÇëÔÚ¿ªÊ¼²Ëµ¥ËÑË÷ Ollama ²¢´ò¿ª
echo.
echo  µÈ´ı·şÎñ¾ÍĞ÷,Ô¼ 5-15 Ãë...
ping -n 10 127.0.0.1 >nul

echo  ÑéÖ¤ Ollama ÊÇ·ñÔÚÏß
curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto ollama_not_running
echo  Ollama ·şÎñÒÑ¾ÍĞ÷
echo.
echo ==============================================
echo   Ollama °²×°³É¹¦
echo   ÏÂÒ»²½: Ë«»÷¸ùÄ¿Â¼ [Ò»¼üÔËĞĞ.bat] ¼´¿ÉÊ¹ÓÃ
echo   Ò²¿ÉÔËĞĞ tools\°²×°Ä£ĞÍ_xxx.bat µ¥¶ÀÏÂÔØÄ£ĞÍ
echo ==============================================
echo.

:already_installed
echo  ¼ì²âµ½ Ollama ÒÑ°²×°
ollama --version
echo.
echo  ÑéÖ¤ Ollama ·şÎñ...
curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1
if not errorlevel 1 goto ollama_running
echo  ¾¯¸æ: Ollama ÒÑ×°µ«·şÎñÎ´ÔËĞĞ
echo  Çë´ò¿ª¿ªÊ¼²Ëµ¥ - Ollama Æô¶¯·şÎñ
echo.
pause
exit /b

:ollama_running
echo  Ollama ·şÎñÔÚÏß,ÎŞĞèÖØ¸´°²×°
echo  ¿ÉÔËĞĞ tools\°²×°Ä£ĞÍ_xxx.bat ÏÂÔØ¸ü¶àÄ£ĞÍ
echo.
pause
exit /b

:download_fail
echo.
echo  ´íÎó: Ollama ÏÂÔØÊ§°Ü (ollama.com + PowerShell ¶¼Ê§°Ü)
echo  ¿ÉÄÜÔ­Òò: ÍøÂç²»Í¨,»ò±»·À»ğÇ½À¹½Ø
echo.
if exist ollama-installer.exe (
    echo  ¼ì²âµ½°ë³ÉÆ· ollama-installer.exe
    dir ollama-installer.exe | findstr ollama-installer
)
echo.
echo  ½â¾ö·½°¸ (°´ÍÆ¼öË³Ğò):
echo    1. ÖØÅÜ±¾ bat [±¾½Å±¾»á´Ó¶ÏµãĞø´« -C - ×Ô¶¯ĞøÏÂÎ´Íê³É²¿·Ö]
echo    2. ä¯ÀÀÆ÷·ÃÎÊ https://ollama.com/download ÏÂÔØ OllamaSetup.exe
echo    3. °ÑÏÂÔØµÄ OllamaSetup.exe ·Åµ½±¾ bat ËùÔÚÄ¿Â¼
echo    4. ÖØÃüÃûÎª ollama-installer.exe ºóÔÙÔËĞĞ´Ë bat
echo.
echo  ½ø½×: PowerShell ÊÖ¶¯Ğø´«ÃüÁî (ÔÚ bat ËùÔÚÄ¿Â¼ÔËĞĞ):
echo    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://ollama.com/download/OllamaSetup.exe','ollama-installer.exe')"
echo.
echo  Ä£ĞÍ (qwen2.5:3b µÈ) ÏÂÔØÒ²»áÓÃÍ¬ÑùµÄ²ßÂÔ (ollama ¹Ù·½Ô´)
echo  ÈçÈÔÓĞÎÊÌâ,¿ÉÁªÏµ¹ÜÀíÔ±Ğ­Öú
echo.
pause
exit /b

:install_fail
echo.
echo  ´íÎó: °²×°Ê§°Ü
echo  ÇëÓÒ¼ü [´Ë bat] - ÒÔ¹ÜÀíÔ±Éí·İÔËĞĞ
echo.
del ollama-installer.exe >nul 2>&1
pause
exit /b

:ollama_not_running
echo.
echo  ¾¯¸æ: Ollama ÒÑ°²×°µ«·şÎñÎ´Æô¶¯
echo  Çë´ò¿ª¿ªÊ¼²Ëµ¥ - ËÑË÷ Ollama - µã»÷ÔËĞĞ
echo  Æô¶¯ºóÔÙ´ÎÔËĞĞ´Ë bat ÑéÖ¤
echo.

echo.
pause
exit /b
