@echo off
chcp 936 >nul
title ÔÆÖÇÊµÑµÖúÊÖ - °²×°ÓïÒôÊ¶±ğ×é¼ş(±¾µØÀëÏß)
cd /d "%~dp0.."

echo [95m==============================================[0m
echo [95m     ÔÆÖÇÊµÑµÖúÊÖ - °²×°ÓïÒôÊ¶±ğ×é¼ş(±¾µØÀëÏß)[0m
echo [95m==============================================[0m
echo.
echo  ÓÃÍ¾: ÖÇÄÜÎÊ´ğÒ³µÄ¡¸Âó¿Ë·çÓïÒôÊäÈë¡¹¹¦ÄÜ
echo  ËµÃ÷: ²ÉÓÃ±¾µØÀëÏßÊ¶±ğÒıÇæ Vosk,ÒôÆµ²»ÉÏ´«ÈÎºÎÍâ²¿·şÎñÆ÷
echo  ×é³É: vosk ¿â [Ô¼ 3MB] + ÖĞÎÄÄ£ĞÍ [Ô¼ 42MB]
echo  Ô¤¼ÆºÄÊ±: Ô¼ 1-3 ·ÖÖÓ [Çå»ªÔ´ + ¹úÄÚ¾µÏñ]
echo.
echo  Êı¾İ±¾µØ»¯³ĞÅµ:
echo    Â¼ÒôÖ»ÔÚä¯ÀÀÆ÷²É¼¯,ËÍ±¾»ú 127.0.0.1 Ê¶±ğ,Ê¶±ğºóÁ¢¼´É¾³ı,
echo    È«³Ì²»ÁªÍø¡¢²»Íâ·¢,·ûºÏÑ§Ğ£Êı¾İ°²È«ÒªÇó¡£
echo.

echo  µÚ 1 ²½: ¼ì²â Python
python --version >nul 2>&1
if errorlevel 1 goto asr_no_py
python --version
echo.
echo  µÚ 2 ²½: °²×° vosk ¿â [Çå»ªÔ´]
python -m pip install vosk -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 python -m pip install vosk
python -c "import vosk" >nul 2>&1
if errorlevel 1 goto asr_fail
echo  vosk ¿â°²×°³É¹¦
echo.
echo  µÚ 3 ²½: ÏÂÔØÖĞÎÄÊ¶±ğÄ£ĞÍ [Ô¼ 42MB]
python "%~dp0_download_vosk.py"
if errorlevel 1 goto asr_model_fail
echo.
echo  µÚ 4 ²½: Ê×´ÎÔËĞĞ»á×Ô¶¯¼ÓÔØÄ£ĞÍ,Ô¼Ğè 5-10 Ãë,ÊôÕı³£ÏÖÏó
echo.
echo  ==============================================
echo   ÓïÒôÊ¶±ğ×é¼ş°²×°Íê³É
echo  ==============================================
echo  Ê¹ÓÃ·½·¨:
echo    1. Ë«»÷¸ùÄ¿Â¼ [Ò»¼üÔËĞĞ.bat] Æô¶¯ÔÆÖÇ
echo    2. ½øÈë [ÖÇÄÜÎÊ´ğ] Ò³Ãæ
echo    3. µãÊäÈë¿òÓÒ²àµÄ [Âó¿Ë·ç] °´Å¥¿ªÊ¼Ëµ»°
echo    4. ËµÍêÔÙµãÒ»´Î [½áÊø],Ê¶±ğ½á¹û×Ô¶¯ÌîÈëÊäÈë¿ò
echo.
echo  ÒÑÖªÏŞÖÆ:
echo    ´¿ÆÕÍ¨»°Ê¶±ğ×¼È·ÂÊ¸ß;Ó¢ÎÄËõĞ´Èç VPC / Docker ¿ÉÄÜÊ¶±ğÎªÒôÒëºº×Ö,
echo    ½¨ÒéÔÚÊäÈë¿òÀïÊÖ¶¯²¹ÕıºóÔÙ·¢ËÍ¡£
goto asr_end

:asr_no_py
echo  ´íÎó: Î´¼ì²âµ½ Python,ÇëÏÈÔËĞĞ tools\°²×°Python.bat
goto asr_end

:asr_fail
echo  ´íÎó: vosk ¿â°²×°Ê§°Ü,Çë¼ì²éÍøÂçºóÖØÊÔ
echo  ÊÖ¶¯ÃüÁî: python -m pip install vosk -i https://pypi.tuna.tsinghua.edu.cn/simple
goto asr_end

:asr_model_fail
echo  ´íÎó: Ä£ĞÍÏÂÔØÊ§°Ü
echo  ¿ÉÉÔºóÖØÅÜ±¾½Å±¾;ÒÑÏÂÔØ²¿·Ö»á×Ô¶¯Ìø¹ı
echo  ÊÖ¶¯ÏÂÔØ: https://alphacephei.com/vosk/models
echo  ÏÂÔØ vosk-model-small-cn-0.22.zip ºó½âÑ¹µ½ models\vosk Ä¿Â¼

:asr_end
if "%~1"=="/silent" exit /b 0

echo.
pause
exit /b
