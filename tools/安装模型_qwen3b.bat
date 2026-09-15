@echo off
chcp 936 >nul
title ÔÆÖÇ - ÏÂÔØÄ£ÐÍ Í¨ÒåÇ§ÎÊ Qwen2.5  3B
cd /d "%~dp0.."

echo [95m==============================================[0m
echo [95m     ÔÆÖÇ - ÏÂÔØÄ£ÐÍ Í¨ÒåÇ§ÎÊ Qwen2.5  3B[0m
echo [95m==============================================[0m
echo.
echo  Ä£ÐÍ: Í¨ÒåÇ§ÎÊ Qwen2.5  3B
echo  ±êÇ©: qwen2.5:3b
echo  ´óÐ¡: Ô¼ 2.0 GB
echo  ËµÃ÷: °¢ÀïÍ¨ÒåÇ§ÎÊ 30 ÒÚ²ÎÊýÇáÁ¿°æ
echo  ³¡¾°: ÈÕ³£ÎÊ´ð  ÍÆ¼ö 4GB ÄÚ´æ
echo.
echo  ÏÂÔØÔ´²ßÂÔ:
echo    1. ¹úÄÚÔ´ modelscope.cn (°¢ÀïÔÆ, ÍÆ¼ö¹úÄÚ»·¾³)
echo    2. Ollama ¹Ù·½ registry (¾³Íâ, Å¼¶û²»ÎÈ)
echo    3. ÈôÁ½¸ö¶¼Ê§°Ü,¸ø³öÊÖ¶¯½Ì³Ì
echo.

echo  µÚ 1 ²½: ¼ì²é Ollama ·þÎñ
where ollama >nul 2>&1
if errorlevel 1 goto no_ollama
curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto ollama_offline
echo  Ollama ÔÚÏß
echo.

echo  µÚ 2 ²½: ¼ì²éÄ£ÐÍÊÇ·ñÒÑ´æÔÚ
ollama list | findstr /I "qwen2.5:3b" >nul 2>&1
if not errorlevel 1 goto already_exists

echo  µÚ 3 ²½: ¿ªÊ¼ÏÂÔØÄ£ÐÍ
echo  ÕýÔÚÀ­È¡ qwen2.5:3b,Ê×´ÎÐèÏÂÔØ Ô¼ 2.0 GB
echo  È¡¾öÓÚÍøËÙ,Ô¼Ðè 3-20 ·ÖÖÓ
echo  ÏÂÔØ¹ý³ÌÖÐÇëÎð¹Ø±Õ´Ë´°¿Ú
echo.
ollama pull qwen2.5:3b
if errorlevel 1 goto pull_fail
echo.
echo  ÏÂÔØÍê³É
echo.

echo  ÑéÖ¤Ä£ÐÍÊÇ·ñ°²×°³É¹¦
ollama list | findstr /I "qwen2.5:3b" >nul 2>&1
if errorlevel 1 goto verify_fail
echo  Ä£ÐÍÒÑ¾ÍÐ÷
echo.
echo ==============================================
echo   Í¨ÒåÇ§ÎÊ Qwen2.5  3B  °²×°³É¹¦
echo ==============================================
echo.
echo  ½ÓÏÂÀ´:
echo    1. Ë«»÷¸ùÄ¿Â¼ [Ò»¼üÔËÐÐ.bat] Æô¶¯ÔÆÖÇ
echo    2. ä¯ÀÀÆ÷·ÃÎÊ http://localhost:5000
echo    3. ¸ÃÄ£ÐÍ»á×Ô¶¯±»µ÷ÓÃ
echo.

:already_exists
echo  ¸ÃÄ£ÐÍÒÑ´æÔÚ,ÎÞÐèÖØ¸´ÏÂÔØ
echo  ÈçÐèÖØ×°,ÇëÏÈÖ´ÐÐ ollama rm qwen2.5:3b
echo.

:no_ollama
echo.
echo  ´íÎó: Î´¼ì²âµ½ Ollama
echo  ÇëÏÈÔËÐÐ tools\°²×°Ollama.bat °²×°·þÎñ
echo.

:ollama_offline
echo.
echo  ´íÎó: Ollama ·þÎñÎ´ÔËÐÐ
echo  Çë´ò¿ª¿ªÊ¼²Ëµ¥ - ËÑË÷ Ollama - Æô¶¯·þÎñ
echo  ·þÎñÆô¶¯ºóÔÙÔËÐÐ´Ë bat
echo.

:pull_fail
echo.
echo  ´íÎó: Ä£ÐÍÏÂÔØÊ§°Ü
echo  ¿ÉÄÜÔ­Òò:
echo    1. ÍøÂç²»ÎÈ¶¨,Ollama Ä¬ÈÏ²Ö¿âÔÚ¾³Íâ
echo    2. ´ÅÅÌ¿Õ¼ä²»×ã,ÐèÖÁÉÙ 5GB ¿ÉÓÃ¿Õ¼ä
echo    3. Ollama ·þÎñÒì³£,ÇëÖØÆô Ollama ºóÖØÊÔ
echo.
echo  ½â¾ö·½°¸ (°´ÍÆ¼öË³Ðò):
echo    ·½·¨ 1: ÖØÊÔ±¾ bat (ÍøÂçÅ¼¶û¶¶¶¯,¶à°ë¹ÜÓÃ)
echo    ·½·¨ 2: ÉÔµÈ¼¸·ÖÖÓÔÙÊÔ,±Ü¿ªÍøÂç¸ß·å
echo    ·½·¨ 3: ¼ì²éÍøÂç´úÀí/·À»ðÇ½ÊÇ·ñÀ¹½ØÁË ollama.com
echo    ·½·¨ 4: »»¸öÐ¡Ä£ÐÍ [Èç deepseek-r1:1.5b ½ö 1.1GB],ÔÙÔËÐÐ±¾ bat
echo    ·½·¨ 5: ÊÖ¶¯ÏÂÔØ GGUF ºóµ¼Èë
echo      1. ·ÃÎÊ https://modelscope.cn (°¢ÀïÔÆ,¹úÄÚ¿É·ÃÎÊ)
echo      2. ËÑË÷²¢ÏÂÔØ¶ÔÓ¦ .gguf ÎÄ¼þ
echo      3. ÐÂ½¨ Modelfile Ð´Èë: FROM ./ÄãµÄÎÄ¼þ.gguf
echo      4. Ö´ÐÐ: ollama create my-model -f Modelfile
echo      5. ÉèÖÃ»·¾³±äÁ¿: set OLLAMA_MODEL=my-model
echo.
echo  ÌáÊ¾: Ä£ÐÍ´æ·ÅÔÚ %USERPROFILE%\.ollama\models [Ollama ¹Ù·½Ô¼¶¨,Îð¸Ä]

:verify_fail
echo.
echo  ´íÎó: Ä£ÐÍÑéÖ¤Ê§°Ü
echo  ÇëÖ´ÐÐ ollama list ²é¿´ÒÑ°²×°Ä£ÐÍ
echo.

echo.
pause
exit /b
