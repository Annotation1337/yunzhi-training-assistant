@echo off
chcp 936 >nul
title ÔÆÖÇÊµÑµÖúÊÖ - Ò»¼üÔËĞĞ
cd /d %~dp0

echo [95m==============================================[0m
echo [95m     ÔÆÖÇÊµÑµÖúÊÖ - Ò»¼üÔËĞĞ[0m
echo [95m==============================================[0m
echo.
if "%~1"=="/auto" set "OC_AUTO=1"
if "%~1"=="/AUTO" set "OC_AUTO=1"
if "%OC_AUTO%"=="1" echo  [È«×Ô¶¯Ä£Ê½] ±ØÑ¡×é¼şÈ±Ê§×Ô¶¯°²×°,¿ÉÑ¡ÏîÄ¬ÈÏ×° qwen2.5:3b
if "%OC_AUTO%"=="1" echo.

echo ----------------------------------------------
echo  [96mµÚ 1 ²½ [±ØÑ¡] ¼ì²â Python »·¾³[0m
echo ----------------------------------------------
python --version >nul 2>&1
if errorlevel 1 goto oc_py_need
python --version
where python
echo  ×´Ì¬: [92mÒÑ°²×°[0m
goto oc_chk_dep

:oc_py_need
echo  ×´Ì¬: Î´°²×° [±ØÑ¡×é¼ş,×Ô¶¯¿ªÊ¼°²×°]
echo  °²×°·½Ê½: winget ÓÅÏÈ,Ê§°Ü»ØÍË»ªÎªÔÆ¾µÏñ/¹ÙÍø
where winget >nul 2>&1
if errorlevel 1 goto oc_py_curl
winget install Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements
if not errorlevel 1 goto oc_py_refresh
echo  winget Ê§°Ü,¸ÄÓÃ°²×°°ü·½Ê½...

:oc_py_curl
set "PYEXE=%TEMP%\yunzhi_py\python-3.11.9-amd64.exe"
if not exist "%TEMP%\yunzhi_py" mkdir "%TEMP%\yunzhi_py"
curl -L -o "%PYEXE%" "https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-amd64.exe" --connect-timeout 30
if exist "%PYEXE%" goto oc_py_install
curl -L -o "%PYEXE%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" --connect-timeout 30
if exist "%PYEXE%" goto oc_py_install
goto oc_py_fail

:oc_py_install
echo  ÕıÔÚ¾²Ä¬°²×°,Ô¼Ğè 1 ·ÖÖÓ,ÇëÎğ¹Ø±Õ´°¿Ú...
if exist "%PYEXE%" "%PYEXE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

:oc_py_refresh
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
python --version >nul 2>&1
if errorlevel 1 goto oc_py_warn
python --version
echo  ×´Ì¬: °²×°³É¹¦
goto oc_chk_dep

:oc_py_warn
echo  Python ÒÑ°²×°µ«µ±Ç°´°¿ÚÎ´Ê¶±ğ,Çë¹Ø±Õ´°¿ÚºóÖØĞÂË«»÷±¾ÎÄ¼ş
goto oc_end

:oc_py_fail
echo  ´íÎó: ×Ô¶¯°²×°Ê§°Ü,ÇëÊÖ¶¯°²×° Python 3.11
echo  ÏÂÔØ: https://www.python.org/downloads/  Îñ±Ø¹´Ñ¡ Add Python to PATH
goto oc_end

:oc_chk_dep
echo.
echo ----------------------------------------------
echo  [96mµÚ 2 ²½ [±ØÑ¡] ¼ì²âºó¶ËÒÀÀµ[0m
echo ----------------------------------------------
python -c "import flask" >nul 2>&1
if errorlevel 1 goto oc_dep_install
python -c "import bs4" >nul 2>&1
if errorlevel 1 goto oc_dep_install
python -c "import PIL" >nul 2>&1
if errorlevel 1 goto oc_dep_install
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 goto oc_dep_install
echo  ×´Ì¬: [92mÒÑ¾ÍĞ÷[0m [flask / Pillow / beautifulsoup4 / matplotlib]

echo.
echo  [96m¿ÉÑ¡ÒÀÀµ¼ì²â[0m: OCR ½ØÍ¼Ê¶±ğ (pytesseract)
python -c "import pytesseract" >nul 2>&1
if errorlevel 1 goto oc_ocr_missing
echo   [92mÒÑ°²×°[0m pytesseract (OCR ¿ÉÓÃ)
goto oc_chk_ollama

:oc_ocr_missing
echo   [93mÎ´°²×°[0m pytesseract [OCR ½ØÍ¼Ê¶±ğ²»¿ÉÓÃ,ÅÅ´íÕï¶ÏÈÔÖ§³ÖÊÖ¶¯ÊäÈë]
echo   Ò»¼ü²¹×°: ÔËĞĞ tools\°²×°OCRÒÀÀµ.bat
echo   »òÃüÁî: python -m pip install pytesseract
echo           ´ËÍâĞè°²×° Tesseract ³ÌĞò: https://github.com/tesseract-ocr/tesseract
goto oc_chk_ollama

:oc_dep_install
echo  ×´Ì¬: [93mÈ±Ê§,×Ô¶¯°²×°ÖĞ[0m [Ô¼ 5MB,Ê×´ÎÔ¼ 1-3 ·ÖÖÓ,Çå»ª¾µÏñÔ´]...
python -m pip install flask Pillow beautifulsoup4 matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 python -m pip install flask Pillow beautifulsoup4 matplotlib
python -c "import flask" >nul 2>&1
if errorlevel 1 goto oc_dep_fail
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 goto oc_dep_fail
echo  ×´Ì¬: [92m°²×°³É¹¦[0m
goto oc_chk_ollama

:oc_dep_fail
echo  [91m´íÎó: ÒÀÀµ°²×°Ê§°Ü[0m,Çë¼ì²éÍøÂçºóÖØĞÂË«»÷±¾ÎÄ¼ş
goto oc_end

:oc_chk_ollama
echo.
echo ----------------------------------------------
echo  [96mµÚ 3 ²½ [¿ÉÑ¡] ¼ì²â Ollama ´óÄ£ĞÍ·şÎñ[0m
echo ----------------------------------------------
where ollama >nul 2>&1
if errorlevel 1 goto oc_ol_missing
echo  ×´Ì¬: [92mÒÑ°²×°[0m
where ollama
ollama --version > "%TEMP%\yz_ver.txt" 2>&1
findstr /V /C:"failed to get console mode" "%TEMP%\yz_ver.txt" 2>nul
curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto oc_ol_off
echo          ·şÎñ×´Ì¬ : [92mÔÚÏß[0m [http://localhost:11434]
set "OC_OLLOK=1"
goto oc_chk_models

:oc_ol_off
echo          ·şÎñ×´Ì¬ : [93mÎ´ÔËĞĞ[0m - Çë´ò¿ª¿ªÊ¼²Ëµ¥ËÑË÷ Ollama µã»÷ÔËĞĞ
goto oc_chk_models

:oc_ol_missing
echo  ×´Ì¬: [93mÎ´°²×°[0m
echo  --------------------------------------------------------------
echo   Ollama ÊÇÊ²Ã´ : ÔÚÄãµçÄÔÉÏ±¾µØÔËĞĞ´óÄ£ĞÍµÄÒıÇæ,ÍÆÀíÈ«³ÌÀëÏß
echo   ×°ÁËÖ®ºó      : ÔÆÖÇ°ÑÁªÍøËÑË÷½á¹û½»¸ø´óÄ£ĞÍ,×Ü½á³ÉÍêÕû»Ø´ğ
echo   ²»×°»áÔõÑù    : ²»Ó°ÏìÊ¹ÓÃ! ÖªÊ¶¿âÎÊ´ğ/ÁªÍøËÑË÷/ÈÎÎñÒıµ¼/
echo                   ÅÅ´íÕï¶Ï/±¨¸æÉú³É È«²¿Õı³£,
echo                   ½öÁªÍø¶µµ×´Ó [Ä£ĞÍ×Ü½á] ½µ¼¶Îª [ÂŞÁĞËÑË÷½á¹û]
echo   ÒÔºóÏë×°      : ÔËĞĞ tools\Ò»¼ü°²×°.bat »ò tools\°²×°Ollama.bat
echo   ×°ÍêÔõÃ´ÅÜ    : ¿ª»ú×Ô¶¯Æô¶¯;ÊÖ¶¯Æô¶¯: ¿ªÊ¼²Ëµ¥ËÑË÷ Ollama
echo  ----------------------------------------------------------------
if exist "%~dp0.yz_skip_ollama" echo   ÌáÊ¾: ÄãÖ®Ç°Ñ¡ÔñÌø¹ı,É¾³ı¸ùÄ¿Â¼ .yz_skip_ollama ¿ÉÖØĞÂÑ¯ÎÊ
if exist "%~dp0.yz_skip_ollama" goto oc_chk_models
if "%OC_AUTO%"=="1" goto oc_ol_do_install

set "ANS="
set /p "ANS=  ÊÇ·ñÏÖÔÚ°²×° Ollama? [1=°²×° / 2=Ìø¹ı²¢¼Ç×¡,»Ø³µÄ¬ÈÏÌø¹ı]: "
if "%ANS%"=="1" goto oc_ol_do_install

:oc_ol_skip_now
echo skipped>"%~dp0.yz_skip_ollama"
if exist "%~dp0.yz_skip_ollama" attrib +h "%~dp0.yz_skip_ollama" >nul 2>&1
echo  ÒÑÌø¹ı²¢¼Ç×¡,ÒÔºó¿ÉÔËĞĞ tools\Ò»¼ü°²×°.bat ²¹×°
goto oc_chk_models

:oc_ol_do_install
echo  ÕıÔÚÏÂÔØ Ollama [À´Ô´ ollama.com Ô­°æ],Ô¼ 200MB...
if exist ollama-installer.exe goto oc_ol_run
curl -L --retry 3 --retry-delay 5 -C - -o ollama-installer.exe --connect-timeout 15 --max-time 3600 https://ollama.com/download/OllamaSetup.exe
if not errorlevel 1 goto oc_ol_run
echo  curl Ê§°Ü,³¢ÊÔ PowerShell...
del ollama-installer.exe >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command try { Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'ollama-installer.exe' -UseBasicParsing } catch { exit 1 }
if not errorlevel 1 goto oc_ol_run
del ollama-installer.exe >nul 2>&1
echo.
echo  ´íÎó: Ollama ÏÂÔØÊ§°Ü
echo  ÇëÊÖ¶¯·ÃÎÊ https://ollama.com/download ÏÂÔØ OllamaSetup.exe
echo  °ÑÏÂÔØµÄÎÄ¼ş·Åµ½±¾Ä¿Â¼²¢ÖØÃüÃûÎª ollama-installer.exe
echo  È»ºóÖØĞÂË«»÷±¾ÎÄ¼ş¼´¿É×Ô¶¯°²×°
goto oc_chk_models

:oc_ol_run
if not exist ollama-installer.exe goto oc_chk_models
echo  ÕıÔÚ¾²Ä¬°²×°,¿ÉÄÜµ¯³ö UAC È·ÈÏ...
ollama-installer.exe /S
del ollama-installer.exe >nul 2>&1
echo  µÈ´ı·şÎñ¾ÍĞ÷,Ô¼ 10-15 Ãë...
ping -n 12 127.0.0.1 >nul
curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto oc_chk_models
set "OC_OLLOK=1"
echo  Ollama °²×°³É¹¦

:oc_chk_models
echo.
echo [96m----------------------------------------------[0m
echo  [96mµÚ 4 ²½ [¿ÉÑ¡] ¼ì²â´óÄ£ĞÍ[0m
echo ----------------------------------------------
if not "%OC_OLLOK%"=="1" goto oc_md_no_ollama

ollama list > "%TEMP%\yz_ml_raw.txt" 2>&1
findstr /V /C:"NAME" /C:"failed to get console mode" "%TEMP%\yz_ml_raw.txt" > "%TEMP%\yz_ml.txt" 2>nul
findstr /C:":" "%TEMP%\yz_ml.txt" >nul 2>&1
if errorlevel 1 goto oc_md_missing
echo  [93mµ±Ç°ÒÑ×°Ä£ĞÍ£º[0m
type "%TEMP%\yz_ml.txt"
echo.
echo  [92m×´Ì¬: ÒÑÓĞ¿ÉÓÃÄ£ĞÍ£¬ÎŞĞèÖØ¸´ÏÂÔØ[0m
echo          Ä£ĞÍÄ¿Â¼ : [96m%USERPROFILE%[0m\.ollama\models
set "OC_MODEL_OK=1"
set "MDMORE="
set /p "MDMORE=  ÊÇ·ñ»¹ÒªÔÙ×°Ò»¸öÄ£ĞÍ? [1=¼ÌĞøÑ¡Ôñ / »Ø³µ=Ìø¹ı]: "
if "%MDMORE%"=="1" goto oc_md_menu
goto oc_chk_sd

:oc_md_missing
echo  [93mµ±Ç°ÒÑ×°Ä£ĞÍ£º[0m(ÎŞ)
echo  [93m×´Ì¬: Î´ÏÂÔØÈÎºÎÄ£ĞÍ[0m
echo    ´óÄ£ĞÍÊÇÊ²Ã´ : »á»Ø´ğµÄÄÔ×Ó,ÏÂÔØºó´æ·ÅÔÚ:
echo                  [96m%USERPROFILE%[0m\.ollama\models
echo    ²»×°»áÔõÑù   : ²»Ó°ÏìºËĞÄ¹¦ÄÜ,ÁªÍø¶µµ×Ö±½ÓÂŞÁĞËÑË÷½á¹û
echo    ÒÔºóÏë×°     : ÔËĞĞ tools\Ò»¼ü°²×°.bat »ò tools\°²×°Ä£ĞÍ_xxx.bat
echo    ÊÍ·Å´ÅÅÌ     : ÃüÁîĞĞÖ´ĞĞ ollama rm Ä£ĞÍÃû ¼´¿ÉÉ¾³ı
if exist "%~dp0.yz_skip_model" echo    ÌáÊ¾: ÄãÖ®Ç°Ñ¡ÔñÌø¹ı,É¾³ı¸ùÄ¿Â¼ .yz_skip_model ¿ÉÖØĞÂÑ¯ÎÊ
if exist "%~dp0.yz_skip_model" goto oc_chk_sd
if "%OC_AUTO%"=="1" set "MDSEL=1" & goto oc_md_pull
goto oc_md_menu

:oc_md_menu
echo  [93mÇëÑ¡ÔñÒªÌí¼Ó/ÏÂÔØµÄÄ£ĞÍ[0m [ÂÌÉ«=±¾»úÒÑ×°,»ÆÉ«=ĞèÏÂÔØ;Ö»Ó°Ïì»Ø´ğÖÊÁ¿,²»Ó°Ïì¹¦ÄÜ]:
<nul set /p "=  [1] qwen2.5:3b          Ô¼ 2.0 GB  ÈÕ³£ÎÊ´ğ  ÍÆ¼ö 4GB ÄÚ´æ  "
findstr /I /C:"qwen2.5:3b" "%TEMP%\yz_ml_raw.txt" >nul 2>&1 && (echo [92m[ÒÑ°²×°][0m) || (echo [93m[ĞèÏÂÔØ][0m)
<nul set /p "=  [2] qwen2.5:7b          Ô¼ 4.7 GB  ¸´ÔÓÍÆÀí  ÍÆ¼ö 8GB ÄÚ´æ »ò 6GB ÏÔ´æ  "
findstr /I /C:"qwen2.5:7b" "%TEMP%\yz_ml_raw.txt" >nul 2>&1 && (echo [92m[ÒÑ°²×°][0m) || (echo [93m[ĞèÏÂÔØ][0m)
<nul set /p "=  [3] deepseek-r1:1.5b    Ô¼ 1.1 GB  ÊıÑ§ÍÆÀí  ÍÆ¼ö 4GB ÄÚ´æ  "
findstr /I /C:"deepseek-r1:1.5b" "%TEMP%\yz_ml_raw.txt" >nul 2>&1 && (echo [92m[ÒÑ°²×°][0m) || (echo [93m[ĞèÏÂÔØ][0m)
<nul set /p "=  [4] glm4:9b             Ô¼ 5.5 GB  ¹¤¾ßµ÷ÓÃ  ÍÆ¼ö 8GB ÄÚ´æ »ò 6GB ÏÔ´æ  "
findstr /I /C:"glm4:9b" "%TEMP%\yz_ml_raw.txt" >nul 2>&1 && (echo [92m[ÒÑ°²×°][0m) || (echo [93m[ĞèÏÂÔØ][0m)
<nul set /p "=  [5] yi:6b               Ô¼ 3.8 GB  Í¨ÓÃ¶Ô»°  ÍÆ¼ö 6GB ÄÚ´æ  "
findstr /I /C:"yi:6b" "%TEMP%\yz_ml_raw.txt" >nul 2>&1 && (echo [92m[ÒÑ°²×°][0m) || (echo [93m[ĞèÏÂÔØ][0m)
<nul set /p "=  [6] qwen2.5-coder:7b    Ô¼ 4.7 GB  ´úÂëÉú³É  ÍÆ¼ö 8GB ÄÚ´æ »ò 6GB ÏÔ´æ  "
findstr /I /C:"qwen2.5-coder:7b" "%TEMP%\yz_ml_raw.txt" >nul 2>&1 && (echo [92m[ÒÑ°²×°][0m) || (echo [93m[ĞèÏÂÔØ][0m)
echo   [0] Ìø¹ı [»Ø³µÄ¬ÈÏ]
set "MDSEL="
set /p "MDSEL=  ÇëÑ¡Ôñ [0-6]: "
if "%MDSEL%"=="1" set "MDSEL_TAG=qwen2.5:3b" & goto oc_md_pull
if "%MDSEL%"=="2" set "MDSEL_TAG=qwen2.5:7b" & goto oc_md_pull
if "%MDSEL%"=="3" set "MDSEL_TAG=deepseek-r1:1.5b" & goto oc_md_pull
if "%MDSEL%"=="4" set "MDSEL_TAG=glm4:9b" & goto oc_md_pull
if "%MDSEL%"=="5" set "MDSEL_TAG=yi:6b" & goto oc_md_pull
if "%MDSEL%"=="6" set "MDSEL_TAG=qwen2.5-coder:7b" & goto oc_md_pull
goto oc_md_skip_now

:oc_md_pull
if "%OC_AUTO%"=="1" set "MDSEL_TAG=qwen2.5:3b"
echo  ÕıÔÚÀ­È¡ [93m%MDSEL_TAG%[0m [Ê×´ÎĞè¼¸·ÖÖÓ,ÇëÎğ¹Ø±Õ´°¿Ú]...
ollama list > "%TEMP%\yz_ml2.txt" 2>&1
findstr /I /C:"%MDSEL_TAG%" "%TEMP%\yz_ml2.txt" >nul 2>&1
if not errorlevel 1 goto oc_md_already
ollama pull %MDSEL_TAG%
if errorlevel 1 goto oc_md_pull_fail
set "OC_MODEL_OK=1"
echo  [92mÄ£ĞÍÏÂÔØÍê³É[0m
goto oc_md_after_pull

:oc_md_already
echo  [92m¸ÃÄ£ĞÍ±¾»úÒÑ°²×°£¬Ìø¹ıÏÂÔØ[0m
set "OC_MODEL_OK=1"
goto oc_md_after_pull

:oc_md_after_pull
echo.
ollama list > "%TEMP%\yz_ml3.txt" 2>&1
findstr /V /B /C:"NAME" /C:"failed" "%TEMP%\yz_ml3.txt" > "%TEMP%\yz_ml.txt" 2>nul
echo  [93mµ±Ç°ÒÑ×°Ä£ĞÍ£º[0m
type "%TEMP%\yz_ml.txt"
goto oc_chk_sd

:oc_md_pull_fail
echo  [91m¾¯¸æ: ÏÂÔØÊ§°Ü[0m [ÍøÂç/´ÅÅÌ/Ollama Òì³£],¿ÉÉÔºóÔËĞĞ tools\Ò»¼ü°²×°.bat ÖØÊÔ
goto oc_chk_sd

:oc_md_skip_now
echo skipped>"%~dp0.yz_skip_model"
if exist "%~dp0.yz_skip_model" attrib +h "%~dp0.yz_skip_model" >nul 2>&1
echo  ÒÑÌø¹ı²¢¼Ç×¡,ÒÔºó¿ÉÔËĞĞ tools\Ò»¼ü°²×°.bat ²¹×°
goto oc_chk_sd

:oc_md_no_ollama
echo  [93m×´Ì¬: Î´ÆôÓÃ[0m [ĞèÒªÏÈ°²×°²¢Æô¶¯ Ollama]
echo    ²»×°»áÔõÑù   : ²»Ó°ÏìºËĞÄ¹¦ÄÜ,ÁªÍø¶µµ×Ö±½ÓÂŞÁĞËÑË÷½á¹û

:oc_chk_sd
echo.
echo ----------------------------------------------
echo  [96mµÚ 5 ²½ [¿ÉÑ¡] ¼ì²â Stable Diffusion »­Í¼Ä£ĞÍ[0m
echo ----------------------------------------------
python -c "import modelscope, torch, diffusers, transformers, accelerate, safetensors, huggingface_hub" >nul 2>&1
if errorlevel 1 goto oc_sd_nodep
if not exist "%CD%\models\sd\runwayml_stable-diffusion-v1-5\model_index.json" goto oc_sd_need_dl
if not exist "%CD%\models\sd\runwayml_stable-diffusion-v1-5\unet\diffusion_pytorch_model.bin" goto oc_sd_need_dl
if not exist "%CD%\models\sd\runwayml_stable-diffusion-v1-5\vae\diffusion_pytorch_model.bin" goto oc_sd_need_dl
if not exist "%CD%\models\sd\runwayml_stable-diffusion-v1-5\text_encoder\pytorch_model.bin" goto oc_sd_need_dl
goto oc_sd_have

echo  ×´Ì¬: [93mÎ´ÏÂÔØ[0m [ÒÀÀµÒÑ¾ÍĞ÷,¿ÉËæÊ±ÏÂÔØ]
echo  ----------------------------------------------------------------
echo   SD ÊÇÊ²Ã´ : ±¾µØÔËĞĞ Stable Diffusion ³ö²å»­µÄÄ£ĞÍ
echo   ²»×°»áÔõÑù: ²»Ó°ÏìºËĞÄ¹¦ÄÜ! ÍØÆËÍ¼ÈÔ¿ÉÓÃ (matplotlib)
echo                ½ö²å»­Àà prompt ×ß SD ³öÍ¼;²»×°Ôò½µ¼¶ÎªÍØÆËÍ¼
echo   ´æ·ÅÎ»ÖÃ  : %CD%\models\sd\runwayml_stable-diffusion-v1-5
echo   ´óĞ¡      : Ô¼ 4.2 GB (¹úÄÚÔ´ÓÅÏÈÏÂÔØ)
echo   ÒÔºóÏë×°  : ÔËĞĞ tools\ÏÂÔØStableDiffusion.bat
echo  ----------------------------------------------------------------
if exist "%~dp0.yz_skip_sd" echo   ÌáÊ¾: ÄãÖ®Ç°Ñ¡ÔñÌø¹ı,É¾³ı¸ùÄ¿Â¼ .yz_skip_sd ¿ÉÖØĞÂÑ¯ÎÊ
if exist "%~dp0.yz_skip_sd" goto oc_chk_asr
if "%OC_AUTO%"=="1" goto oc_sd_install

set "SD_ANS="
set /p "SD_ANS=  ÊÇ·ñÏÖÔÚÏÂÔØ SD Ä£ĞÍ? [1=ÏÂÔØ / 2=Ìø¹ı²¢¼Ç×¡,»Ø³µÄ¬ÈÏÌø¹ı]: "
if "%SD_ANS%"=="1" goto oc_sd_install
goto oc_sd_skip

:oc_sd_nodep
echo  [93m×´Ì¬: ²å»­¹¦ÄÜÒÀÀµÈ±Ê§[0m [È±ÉÙ PyTorch / diffusers]
echo  ----------------------------------------------------------------
if "%OC_AUTO%"=="1" goto oc_sd_dep_install_auto
echo   Ô­Òò    : ³ö²å»­ĞèÒª PyTorch + diffusers,µ±Ç°¼ì²âµ½Î´°²×°
echo   Ó°Ïì    : ½ö¡¸²å»­¡¹³öÍ¼²»¿ÉÓÃ;ÍØÆË/¼Ü¹¹Í¼ (matplotlib) ²»ÊÜÓ°Ïì
echo   Ò»¼ü²¹×°: ÔËĞĞ tools\°²×°»­Í¼ÒÀÀµ.bat (Ô¼ 2-3GB,¹úÄÚÔ´)  <== ÍÆ¼ö
echo   »òÃüÁî  : python -m pip install torch diffusers transformers accelerate
echo             safetensors -i https://pypi.tuna.tsinghua.edu.cn/simple
echo  ----------------------------------------------------------------
goto oc_chk_asr

:oc_sd_dep_install_auto
echo  [93m[×Ô¶¯Ä£Ê½] ÕıÔÚ°²×° PyTorch + diffusers (Ô¼ 2-3GB,Ê×´ÎĞè 5-15 ·ÖÖÓ)[0m...
echo.
call "%~dp0tools\°²×°»­Í¼ÒÀÀµ.bat"
echo.
python -c "import modelscope, torch, diffusers, transformers, accelerate, safetensors, huggingface_hub" >nul 2>&1
if errorlevel 1 goto oc_sd_nodep_after_install
echo  [92mÒÀÀµ×°ºÃÁË£¬ÏÖÔÚ¿ªÊ¼ÏÂÔØ SD Ä£ĞÍ...[0m
goto oc_sd_install

:oc_sd_nodep_after_install
echo  [91m[×Ô¶¯Ä£Ê½] ÒÀÀµ°²×°Ê§°Ü[0m,Ìø¹ı SD,½µ¼¶Îª¡¸ÍØÆËÍ¼¡¹Ä£Ê½
echo  ----------------------------------------------------------------
echo   Ó°Ïì    : ½ö¡¸²å»­¡¹³öÍ¼²»¿ÉÓÃ;ÍØÆË/¼Ü¹¹Í¼ (matplotlib) ²»ÊÜÓ°Ïì
echo   ÒÔºóÏë×°: ÔËĞĞ tools\°²×°»­Í¼ÒÀÀµ.bat ÖØÊÔ
echo  ----------------------------------------------------------------
goto oc_chk_asr

:oc_sd_need_dl
echo  ×´Ì¬: [93mÎ´ÏÂÔØ[0m [ÒÀÀµÒÑ¾ÍĞ÷,¿ÉËæÊ±ÏÂÔØ]
echo  ----------------------------------------------------------------
echo   SD ÊÇÊ²Ã´ : ±¾µØÔËĞĞ Stable Diffusion ³ö²å»­µÄÄ£ĞÍ
echo   ²»×°»áÔõÑù: ²»Ó°ÏìºËĞÄ¹¦ÄÜ! ÍØÆËÍ¼ÈÔ¿ÉÓÃ (matplotlib)
echo                ½ö²å»­Àà prompt ×ß SD ³öÍ¼;²»×°Ôò½µ¼¶ÎªÍØÆËÍ¼
echo   ´æ·ÅÎ»ÖÃ  : %CD%\models\sd\runwayml_stable-diffusion-v1-5
echo   ´óĞ¡      : Ô¼ 4.2 GB (¹úÄÚÔ´ÓÅÏÈÏÂÔØ)
echo   ÒÔºóÏë×°  : ÔËĞĞ tools\ÏÂÔØStableDiffusion.bat
echo  ----------------------------------------------------------------
if exist "%~dp0.yz_skip_sd" echo   ÌáÊ¾: ÄãÖ®Ç°Ñ¡ÔñÌø¹ı,É¾³ı¸ùÄ¿Â¼ .yz_skip_sd ¿ÉÖØĞÂÑ¯ÎÊ
if exist "%~dp0.yz_skip_sd" goto oc_chk_asr
if "%OC_AUTO%"=="1" goto oc_sd_install

set "SD_ANS="
set /p "SD_ANS=  ÊÇ·ñÏÖÔÚÏÂÔØ SD Ä£ĞÍ? [1=ÏÂÔØ / 2=Ìø¹ı²¢¼Ç×¡,»Ø³µÄ¬ÈÏÌø¹ı]: "
if "%SD_ANS%"=="1" goto oc_sd_install
goto oc_sd_skip

:oc_sd_install
echo  ÕıÔÚµ÷ÓÃ tools\ÏÂÔØStableDiffusion.bat ...
call "%~dp0tools\ÏÂÔØStableDiffusion.bat"
goto oc_sd_done

:oc_sd_skip
echo skipped>"%~dp0.yz_skip_sd"
if exist "%~dp0.yz_skip_sd" attrib +h "%~dp0.yz_skip_sd" >nul 2>&1
echo  ÒÑÌø¹ı²¢¼Ç×¡,ÒÔºó¿ÉÔËĞĞ tools\ÏÂÔØStableDiffusion.bat ²¹×°
goto oc_chk_asr

:oc_sd_have
echo  ×´Ì¬: [92mÒÑÏÂÔØ[0m [ÒÀÀµÒÑ¾ÍĞ÷]
set "OC_SD_OK=1"
echo          Ä£ĞÍÄ¿Â¼ : %CD%\models\sd\runwayml_stable-diffusion-v1-5

:oc_sd_done
:oc_chk_asr
echo.
echo ----------------------------------------------
echo  [96mµÚ 6 ²½ [¿ÉÑ¡] ¼ì²âÓïÒôÊ¶±ğ×é¼ş[0m
echo ----------------------------------------------
python -c "import vosk" >nul 2>&1
if errorlevel 1 goto oc_asr_missing
if not exist "%~dp0models\vosk\am\final.mdl" goto oc_asr_missing
echo  ×´Ì¬: [92mÒÑ¾ÍĞ÷[0m [Âó¿Ë·çÓïÒôÊäÈë¿ÉÓÃ,±¾µØÀëÏßÊ¶±ğ,ÒôÆµ²»Íâ·¢]
set "OC_ASR_OK=1"
goto oc_summary

:oc_asr_missing
echo  ×´Ì¬: [93mÎ´ÆôÓÃ[0m [ÓïÒôÊäÈë²»¿ÉÓÃ,¼üÅÌÊäÈëÍêÈ«²»ÊÜÓ°Ïì]
echo  ----------------------------------------------------------------
echo   ÓïÒôÊäÈëÊÇÊ²Ã´: ÖÇÄÜÎÊ´ğÒ³µãÂó¿Ë·ç,ÓÃÆÕÍ¨»°Ö±½ÓËµ»°ÌáÎÊ
echo   ×°ÁËÖ®ºó      : Ñ§Éú²»ÓÃ´ò×Ö,ËµÍê×Ô¶¯×ª³ÉÎÄ×ÖÌî½øÊäÈë¿ò
echo   ²»×°»áÔõÑù    : ²»Ó°ÏìÈÎºÎ¹¦ÄÜ,Ñ§ÉúÈÔ¿É¼üÅÌÊäÈëÎÊÌâ
echo   ´óĞ¡          : Ô¼ 45MB [¿â 3MB + ÖĞÎÄÄ£ĞÍ 42MB],Ô¼ 1-3 ·ÖÖÓ
echo   Êı¾İËµÃ÷      : ´¿±¾µØÀëÏßÊ¶±ğ,ÒôÆµ²»ÉÏ´«ÈÎºÎÍâ²¿·şÎñÆ÷
echo   ÒÔºóÏë×°      : ÔËĞĞ tools\°²×°ÓïÒôÊ¶±ğ.bat
echo  ----------------------------------------------------------------
if exist "%~dp0.yz_skip_asr" echo   ÌáÊ¾: ÄãÖ®Ç°Ñ¡ÔñÌø¹ı,É¾³ı¸ùÄ¿Â¼ .yz_skip_asr ¿ÉÖØĞÂÑ¯ÎÊ
if exist "%~dp0.yz_skip_asr" goto oc_summary
if "%OC_AUTO%"=="1" goto oc_asr_install

set "ASR_ANS="
set /p "ASR_ANS=  ÊÇ·ñ°²×°ÓïÒôÊ¶±ğ×é¼ş? [1=°²×°(ÍÆ¼ö) / 2=Ìø¹ı²¢¼Ç×¡,»Ø³µÄ¬ÈÏ°²×°]: "
if "%ASR_ANS%"=="2" goto oc_asr_skip
goto oc_asr_install

:oc_asr_install
echo.
echo  [96mÕıÔÚ°²×°ÓïÒôÊ¶±ğ×é¼ş [Ô¼ 45MB],ÇëÉÔºò 1-3 ·ÖÖÓ...[0m
set "OC_PWD=%CD%"
call "%~dp0tools\°²×°ÓïÒôÊ¶±ğ.bat" /silent
cd /d "%OC_PWD%"
python -c "import vosk" >nul 2>&1
if errorlevel 1 goto oc_asr_fail
if not exist "%~dp0models\vosk\am\final.mdl" goto oc_asr_fail
set "OC_ASR_OK=1"
echo  [92mÓïÒôÊ¶±ğ×é¼ş°²×°Íê³É,Âó¿Ë·çÓïÒôÊäÈëÒÑ¿ÉÓÃ[0m
goto oc_summary

:oc_asr_fail
echo  [91mÓïÒôÊ¶±ğ×é¼ş°²×°Ê§°Ü[0m [²»Ó°ÏìÆäËû¹¦ÄÜ]
echo    ¿ÉÉÔºóÔËĞĞ tools\°²×°ÓïÒôÊ¶±ğ.bat ÖØÊÔ,»òÖ±½ÓÓÃ¼üÅÌÊäÈëÎÊÌâ
goto oc_summary

:oc_asr_skip
echo skipped>"%~dp0.yz_skip_asr"
if exist "%~dp0.yz_skip_asr" attrib +h "%~dp0.yz_skip_asr" >nul 2>&1
echo  ÒÑÌø¹ı²¢¼Ç×¡,ÒÔºó¿ÉÔËĞĞ tools\°²×°ÓïÒôÊ¶±ğ.bat ²¹×°
goto oc_summary

:oc_summary
set "OKTXT=[92m¿ÉÓÃ[0m"
set "NOTXT=[93mÎ´ÆôÓÃ[0m"
echo.
echo ----------------------------------------------
echo  [96m¼ì²âÍê³É - µ±Ç°¿ÉÓÃ¹¦ÄÜ[0m
echo ----------------------------------------------
echo   ÖªÊ¶¿âÎÊ´ğ / ÈÎÎñÒıµ¼ / ÅÅ´íÕï¶Ï / ±¨¸æÉú³É : [92m¿ÉÓÃ[0m
echo   ÁªÍøËÑË÷¶µµ×                               : [92m¿ÉÓÃ[0m
echo   ÍØÆË/¼Ü¹¹Í¼ (matplotlib)                   : [92m¿ÉÓÃ[0m
if "%OC_SD_OK%"=="1" echo   ²å»­³öÍ¼ (Stable Diffusion)               : %OKTXT%
if not "%OC_SD_OK%"=="1" echo   ²å»­³öÍ¼ (Stable Diffusion)               : %NOTXT%
if "%OC_MODEL_OK%"=="1" echo   ´óÄ£ĞÍ×Ü½á»Ø´ğ                             : %OKTXT%
if not "%OC_MODEL_OK%"=="1" echo   ´óÄ£ĞÍ×Ü½á»Ø´ğ                             : %NOTXT%
if "%OC_ASR_OK%"=="1" echo   ÓïÒôÊäÈë (Vosk ±¾µØÀëÏß)                  : %OKTXT%
if not "%OC_ASR_OK%"=="1" echo   ÓïÒôÊäÈë (Vosk ±¾µØÀëÏß)                  : %NOTXT%
echo   [93mÌáÊ¾: ÒÔÉÏ¡¸Î´ÆôÓÃ¡¹Ïî²»Ó°ÏìÆäËû¹¦ÄÜ,¿ÉËæÊ±²¹×°[0m
if "%OC_AUTO%"=="1" goto oc_launch

set "LA="
set /p "LA=  °´»Ø³µÁ¢¼´Æô¶¯ÔÆÖÇ [»òÊäÈë 2 ÍË³ö]: "
if "%LA%"=="2" goto oc_quit

:oc_launch
echo.
echo  [96mÆô¶¯Ç°×Ô¼ì[0m: É¨ÃèËùÓĞÒÀÀµ...
python check_deps.py
echo.
echo  [92mÕıÔÚÆô¶¯[0m,ä¯ÀÀÆ÷½«×Ô¶¯´ò¿ª http://localhost:5000
echo  ¹Ø±Õ±¾´°¿Ú¼´Í£Ö¹·şÎñ
echo.
python app.py
goto oc_end

:oc_quit
echo  ÒÑÍË³ö¡£ÒÔºóÊ¹ÓÃÖ»ĞèË«»÷±¾ÎÄ¼ş¡£

:oc_end
echo.
pause
exit /b
