@echo off
chcp 936 >nul
title ÔÆÖÇÊµÑµÖúÊÖ - »·¾³Ò»¼ü°²×°Ïòµ¼
cd /d "%~dp0.."

echo [95m==============================================[0m
echo [95m     ÔÆÖÇÊµÑµÖúÊÖ - »·¾³Ò»¼ü°²×°Ïòµ¼[0m
echo [95m==============================================[0m
echo.
echo  ±¾Ïòµ¼Ò»´ÎĞÔ×°ÆëÔËĞĞ»·¾³
echo  [±¾ÎÄ¼şÎ»ÓÚ tools Ä¿Â¼,ÈÕ³£Ê¹ÓÃÖ»ĞèË«»÷¸ùÄ¿Â¼ Ò»¼üÔËĞĞ.bat]
echo.
echo  [±ØÑ¡] Python »·¾³
echo    ×÷ÓÃ      : ÔÆÖÇºó¶Ë³ÌĞòµÄÔËĞĞ»ù´¡
echo    ²»×°»áÔõÑù: ÏµÍ³ÍêÈ«ÎŞ·¨Æô¶¯,ÊôÓÚ±Ø×° [×Ô¶¯¼ì²âÈ±ÁË²Å×°]
echo    ´æ·ÅÎ»ÖÃ  : %LOCALAPPDATA%\Programs\Python\Python311
echo    ÔõÃ´ÔËĞĞ  : °²×°Ê±×Ô¶¯¼ÓÈë PATH,Ö®ºóÈÎÒâ´°¿ÚÇÃ python ¼´¿É
echo.
echo  [±ØÑ¡] ºó¶ËÒÀÀµ
echo    ×÷ÓÃ      : flask ÍøÕ¾¿ò¼Ü / beautifulsoup4 ÁªÍøËÑË÷½âÎö µÈ
echo    ²»×°»áÔõÑù: ÏµÍ³ÎŞ·¨Æô¶¯,ÊôÓÚ±Ø×° [×Ô¶¯¼ì²âÈ±ÁË²Å×°]
echo.
echo  [¿ÉÑ¡] Ollama ´óÄ£ĞÍ·şÎñ
echo    ×÷ÓÃ      : ÔÚÄãµçÄÔÉÏ±¾µØÔËĞĞ´óÄ£ĞÍµÄÒıÇæ,ÍÆÀíÈ«³ÌÀëÏß
echo    ²»×°»áÔõÑù: ²»Ó°ÏìÊ¹ÓÃ! ÖªÊ¶¿âÎÊ´ğ/ÁªÍøËÑË÷/ÈÎÎñÒıµ¼/
echo                ÅÅ´íÕï¶Ï/±¨¸æÉú³É È«²¿Õı³£,
echo                ½öÁªÍø¶µµ×´Ó [Ä£ĞÍ×Ü½á] ½µ¼¶Îª [ÂŞÁĞËÑË÷½á¹û]
echo    ´æ·ÅÎ»ÖÃ  : %LOCALAPPDATA%\Programs\Ollama
echo    ÔõÃ´ÔËĞĞ  : ¿ª»ú×Ô¶¯Æô¶¯;ÊÖ¶¯Æô¶¯: ¿ªÊ¼²Ëµ¥ËÑË÷ Ollama
echo.
echo  [¿ÉÑ¡] ´óÄ£ĞÍÏÂÔØ 6 Ñ¡ 1
echo    ×÷ÓÃ      : »á»Ø´ğµÄÄÔ×Ó,°´µçÄÔÄÚ´æÑ¡Ôñ,ÍÆ¼ö qwen2.5:3b
echo    ²»×°»áÔõÑù: ²»Ó°ÏìºËĞÄ¹¦ÄÜ,ÁªÍø¶µµ×Ö±½ÓÂŞÁĞËÑË÷½á¹û
echo    ´æ·ÅÎ»ÖÃ  : %USERPROFILE%\.ollama\models
echo    ÊÍ·Å´ÅÅÌ  : ÃüÁîĞĞÖ´ĞĞ ollama rm Ä£ĞÍÃû ¼´¿ÉÉ¾³ı
echo.
if "%~1"=="/auto" set "AUTO_MODE=1"
if "%~1"=="/AUTO" set "AUTO_MODE=1"
if "%AUTO_MODE%"=="1" echo  *** È«×Ô¶¯Ä£Ê½: ±ØÑ¡×é¼ş + Ollama + qwen2.5:3b ×Ô¶¯×°Æë ***
if "%AUTO_MODE%"=="1" echo.

echo ----------------------------------------------
echo  [±ØÑ¡ 1/2] ¼ì²é Python »·¾³
echo ----------------------------------------------
python --version >nul 2>&1
if errorlevel 1 goto py_need
python --version
echo  Python ÒÑ¾ÍĞ÷
goto step_dep

:py_need
echo  Î´¼ì²âµ½ Python,¿ªÊ¼×Ô¶¯°²×°...
where winget >nul 2>&1
if errorlevel 1 goto py_curl
echo  ÕıÔÚÍ¨¹ı winget °²×° Python 3.11,ÇëÉÔºò...
winget install Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements
if not errorlevel 1 goto py_refresh
echo  winget °²×°Ê§°Ü,¸ÄÓÃÏÂÔØ°²×°°ü·½Ê½
echo.

:py_curl
set "PYEXE=%TEMP%\yunzhi_py\python-3.11.9-amd64.exe"
if not exist "%TEMP%\yunzhi_py" mkdir "%TEMP%\yunzhi_py"
echo  ÕıÔÚ´Ó»ªÎªÔÆ¾µÏñÏÂÔØ Python 3.11 °²×°°ü...
curl -L -o "%PYEXE%" "https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-amd64.exe" --connect-timeout 30
if exist "%PYEXE%" goto py_install
echo  »ªÎªÔÆ¾µÏñÊ§°Ü,³¢ÊÔ Python ¹ÙÍø...
curl -L -o "%PYEXE%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" --connect-timeout 30
if exist "%PYEXE%" goto py_install
goto py_fail

:py_install
echo  ÕıÔÚ¾²Ä¬°²×° Python,Ô¼Ğè 1 ·ÖÖÓ,ÇëÎğ¹Ø±Õ´°¿Ú...
if "%AUTO_MODE%"=="1" echo  [auto] ºóÌ¨°²×°ÖĞ,Íê³Éºó×Ô¶¯¼ÌĞø
set "PYEXE=%TEMP%\yunzhi_py\python-3.11.9-amd64.exe"
if exist "%PYEXE%" "%PYEXE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

:py_refresh
echo  ÕıÔÚË¢ĞÂµ±Ç°´°¿ÚµÄ PATH...
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
python --version >nul 2>&1
if errorlevel 1 goto py_path_warn
python --version
echo  Python °²×°³É¹¦
goto step_dep

:py_path_warn
echo  ¾¯¸æ: Python ÒÑ°²×°,µ«µ±Ç°´°¿ÚÎ´ÄÜÁ¢¼´Ê¶±ğ
echo  Çë¹Ø±Õ±¾´°¿Ú,ÖØĞÂË«»÷±¾Ïòµ¼,»á×Ô¶¯´ÓÏÂÒ»²½¼ÌĞø
goto end_pause

:py_fail
echo  ´íÎó: Python ×Ô¶¯°²×°Ê§°Ü
echo  ÇëÊÖ¶¯°²×° Python 3.11:
echo    1. ´ò¿ª https://www.python.org/downloads/
echo    2. °²×°Ê±Îñ±Ø¹´Ñ¡ Add Python to PATH
echo    3. Íê³ÉºóÖØĞÂÔËĞĞ±¾Ïòµ¼
goto end_pause

:step_dep
echo.
echo ----------------------------------------------
echo  [±ØÑ¡ 2/2] ¼ì²éºó¶ËÒÀÀµ
echo ----------------------------------------------
python -c "import flask" >nul 2>&1
if errorlevel 1 goto dep_install
python -c "import bs4" >nul 2>&1
if errorlevel 1 goto dep_install
python -c "import PIL" >nul 2>&1
if errorlevel 1 goto dep_install
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 goto dep_install
echo  ÒÀÀµÒÑ¾ÍĞ÷ [flask / Pillow / bs4 / matplotlib]
goto step_ollama

:dep_install
echo  ÕıÔÚ°²×°ÒÀÀµ flask / Pillow / beautifulsoup4 / matplotlib ...
echo  Ê×´ÎÔ¼Ğè 1-3 ·ÖÖÓ,ÓÅÏÈÊ¹ÓÃÇå»ª¾µÏñÔ´...
python -m pip install flask Pillow beautifulsoup4 matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 python -m pip install flask Pillow beautifulsoup4 matplotlib
python -c "import flask" >nul 2>&1
if errorlevel 1 goto dep_fail
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 goto dep_fail
echo  ÒÀÀµ°²×°³É¹¦
goto step_ollama

:dep_fail
echo  ´íÎó: ÒÀÀµ°²×°Ê§°Ü,Çë¼ì²éÍøÂçºóÖØĞÂÔËĞĞ±¾Ïòµ¼
goto end_pause

:step_ollama
echo.
echo ----------------------------------------------
echo  [¿ÉÑ¡ 1/2] Ollama ´óÄ£ĞÍ·şÎñ
echo ----------------------------------------------
echo  ×÷ÓÃ: ÔÚ±¾»úÔËĞĞ´óÄ£ĞÍ,°Ñ»Ø´ğ×Ü½áµÃ¸üÍêÕû×ÔÈ»
echo  ²»°²×°: ÈÔ¿ÉÕı³£Ê¹ÓÃ ÖªÊ¶¿âÎÊ´ğ + ÁªÍøËÑË÷¶µµ×
if "%AUTO_MODE%"=="1" goto ol_check

set "ANS="
set /p "ANS=  ÊÇ·ñ°²×° Ollama? [1=°²×° / 2=Ìø¹ı,»Ø³µÄ¬ÈÏÌø¹ı]: "
if "%ANS%"=="1" goto ol_check
goto ol_skip

:ol_check
where ollama >nul 2>&1
if errorlevel 1 goto ol_download
goto ol_already

:ol_download
echo  ÕıÔÚÏÂÔØ Ollama °²×°°ü [À´Ô´ ollama.com Ô­°æ],Ô¼ 200MB...
if exist ollama-installer.exe goto ol_run
curl -L --retry 3 --retry-delay 5 -C - -o ollama-installer.exe --connect-timeout 15 --max-time 3600 https://ollama.com/download/OllamaSetup.exe
if not errorlevel 1 goto ol_run
echo  curl Ê§°Ü,³¢ÊÔ PowerShell...
del ollama-installer.exe >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command try { Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'ollama-installer.exe' -UseBasicParsing } catch { exit 1 }
if not errorlevel 1 goto ol_run
del ollama-installer.exe >nul 2>&1
goto ol_dl_fail

:ol_run
if not exist ollama-installer.exe goto ol_dl_fail
echo  ÕıÔÚ¾²Ä¬°²×° Ollama,¿ÉÄÜµ¯³ö UAC È·ÈÏ...
ollama-installer.exe /S
del ollama-installer.exe >nul 2>&1
echo  µÈ´ı·şÎñ¾ÍĞ÷,Ô¼ 10-15 Ãë...
ping -n 12 127.0.0.1 >nul
curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto ol_not_running
echo  Ollama °²×°²¢Æô¶¯³É¹¦
goto step_model

:ol_already
ollama --version
curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto ol_not_running
echo  Ollama ÒÑ°²×°ÇÒ·şÎñÔÚÏß
goto step_model

:ol_skip
echo  ÒÑÌø¹ı Ollama °²×° [Ä£ĞÍÏÂÔØĞèÒª Ollama,Ò»²¢Ìø¹ı]
goto ask_launch

:ol_not_running
echo  ¾¯¸æ: Ollama ÒÑ°²×°µ«·şÎñÎ´ÔËĞĞ
echo  Çë´ò¿ª¿ªÊ¼²Ëµ¥ - ËÑË÷ Ollama - µã»÷ÔËĞĞ
goto md_no_ollama

:ol_dl_fail
echo  ´íÎó: Ollama ÏÂÔØÊ§°Ü,¿ÉÉÔºóÖØÊÔ»òÊÖ¶¯°²×°:
echo    1. ·ÃÎÊ https://ollama.com/download ÏÂÔØ OllamaSetup.exe
echo    2. ·Åµ½±¾Ä¿Â¼²¢ÖØÃüÃûÎª ollama-installer.exe,ÔÙÔËĞĞ±¾Ïòµ¼
goto end_pause

:step_model
echo.
echo ----------------------------------------------
echo  [¿ÉÑ¡ 2/2] ÏÂÔØ´óÄ£ĞÍ [6 Ñ¡ 1]
echo ----------------------------------------------
if "%AUTO_MODE%"=="1" set "MODEL_TAG=qwen2.5:3b" & goto md_pull
echo  °´µçÄÔÄÚ´æÑ¡Ò»¸ö¼´¿É,Ò²¿ÉÌø¹ı,²»Ó°ÏìÖªÊ¶¿âÓëÁªÍø¹¦ÄÜ:
echo   [1] qwen2.5:3b          Ô¼ 2.0 GB  ÈÕ³£ÎÊ´ğ  ÍÆ¼ö 4GB ÄÚ´æ
echo   [2] qwen2.5:7b          Ô¼ 4.7 GB  ¸´ÔÓÍÆÀí  ÍÆ¼ö 8GB ÄÚ´æ »ò 6GB ÏÔ´æ
echo   [3] deepseek-r1:1.5b    Ô¼ 1.1 GB  ÊıÑ§ÍÆÀí  ÍÆ¼ö 4GB ÄÚ´æ
echo   [4] glm4:9b             Ô¼ 5.5 GB  ¹¤¾ßµ÷ÓÃ  ÍÆ¼ö 8GB ÄÚ´æ »ò 6GB ÏÔ´æ
echo   [5] yi:6b               Ô¼ 3.8 GB  Í¨ÓÃ¶Ô»°  ÍÆ¼ö 6GB ÄÚ´æ
echo   [6] qwen2.5-coder:7b    Ô¼ 4.7 GB  ´úÂëÉú³É  ÍÆ¼ö 8GB ÄÚ´æ »ò 6GB ÏÔ´æ
echo   [0] Ìø¹ı [»Ø³µÄ¬ÈÏ]

set "MD="
set /p "MD=  ÇëÑ¡Ôñ [0-6]: "
if "%MD%"=="1" set "MODEL_TAG=qwen2.5:3b" & goto md_pull
if "%MD%"=="2" set "MODEL_TAG=qwen2.5:7b" & goto md_pull
if "%MD%"=="3" set "MODEL_TAG=deepseek-r1:1.5b" & goto md_pull
if "%MD%"=="4" set "MODEL_TAG=glm4:9b" & goto md_pull
if "%MD%"=="5" set "MODEL_TAG=yi:6b" & goto md_pull
if "%MD%"=="6" set "MODEL_TAG=qwen2.5-coder:7b" & goto md_pull
goto md_skip

:md_pull
echo.
echo  ÕıÔÚÀ­È¡ %MODEL_TAG% ...
ollama list | findstr /I "%MODEL_TAG%" >nul 2>&1
if not errorlevel 1 goto md_exists
echo  ÏÂÔØÖĞ,È¡¾öÓÚÍøËÙÔ¼Ğè 3-20 ·ÖÖÓ,ÇëÎğ¹Ø±Õ´°¿Ú...
ollama pull %MODEL_TAG%
if errorlevel 1 goto md_pull_fail
echo  Ä£ĞÍÏÂÔØÍê³É,´óÄ£ĞÍ¾ÍĞ÷
goto ask_launch

:md_exists
echo  ¸ÃÄ£ĞÍÒÑ´æÔÚ,ÎŞĞèÖØ¸´ÏÂÔØ
goto ask_launch

:md_skip
echo  ÒÑÌø¹ıÄ£ĞÍÏÂÔØ [²»×°Ä£ĞÍÒ²ÄÜÓÃ: ÖªÊ¶¿â+ÁªÍø¶µµ×]
goto ask_launch

:md_no_ollama
echo  ÒÑÌø¹ıÄ£ĞÍÏÂÔØ [ĞèÏÈ×°ºÃ²¢Æô¶¯ Ollama]

:md_pull_fail
echo  ¾¯¸æ: Ä£ĞÍÏÂÔØÊ§°Ü [ÍøÂç²»ÎÈ/´ÅÅÌ²»×ã/Ollama Òì³£]
echo  ¿ÉÉÔºóÖØÅÜ±¾Ïòµ¼,²»Ó°ÏìÆäËû¹¦ÄÜ

:ask_launch
echo.
if "%AUTO_MODE%"=="1" goto do_launch
set "LA="
set /p "LA=  ÊÇ·ñÁ¢¼´Æô¶¯ÔÆÖÇ? [1=Æô¶¯,»Ø³µÄ¬ÈÏ / 2=ÍË³ö]: "
if "%LA%"=="2" goto end_quit

:do_launch
echo.
echo  ÕıÔÚÆô¶¯ÔÆÖÇ... ä¯ÀÀÆ÷½«×Ô¶¯´ò¿ª http://localhost:5000
echo  ¹Ø±Õ±¾´°¿Ú¼´Í£Ö¹·şÎñ
echo.
python app.py
goto end_pause

:end_quit
echo  Ïòµ¼½áÊø¡£Ö®ºóË«»÷¸ùÄ¿Â¼ [Ò»¼üÔËĞĞ.bat] ¼´¿ÉÔËĞĞÔÆÖÇ

:end_pause
echo.
pause
exit /b
