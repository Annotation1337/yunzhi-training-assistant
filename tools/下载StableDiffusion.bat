@echo off
chcp 936 >nul
title ÔÆÖÇ - ÏÂÔØ Stable Diffusion Ä£ĞÍ(ÖÇÄÜ¼ÓËÙ°æ)
cd /d "%~dp0.."

echo [95m==============================================[0m
echo [95m     ÔÆÖÇ - ÏÂÔØ Stable Diffusion Ä£ĞÍ(ÖÇÄÜ¼ÓËÙ°æ)[0m
echo [95m==============================================[0m
echo.
echo  Ä£ĞÍ: runwayml/stable-diffusion-v1-5 (±ê×¼°æ ~3.2GB)
echo  ÓÃÍ¾: ±¾µØ AI ³öÍ¼(ÍØÆËÍ¼ÈÔ¿ÉÓÃ matplotlib)
echo  ´æ·ÅÎ»ÖÃ: %CD%\models\sd\runwayml_stable-diffusion-v1-5
echo.
echo  ¼ÓËÙ²ßÂÔ(Èı¼¶»ØÍË,¹úÄÚ»·¾³ÎÈÈç¹·):
echo    1. ModelScope ¹Ù·½¾µÏñ (°¢ÀïÔÆ CDN,Ê×Ñ¡,×î¿ì×îÎÈ)
echo    2. hf-mirror.com ¹úÄÚ HF ¾µÏñ (»ØÍË)
echo    3. huggingface.co Ô­°æ (×îºó¶µµ×,¹úÄÚ¶à²»Í¨)
echo    4. Python 4 Ïß³Ì²¢·¢ + ¶ÏµãĞø´«(±È curl ¿ì 5-10x)
echo    5. ÖÇÄÜÖØÊÔ:µ¥ÎÄ¼ş³¬Ê±×Ô¶¯Ğø´«,²»È«ÖØÀ´
echo    6. ÒÑÏÂÔØÎÄ¼ş×Ô¶¯Ìø¹ı
echo.

echo  µÚ 1 ²½: ¼ì²éÊÇ·ñÒÑÏÂÔØ
if exist "%CD%\models\sd\runwayml_stable-diffusion-v1-5\unet\diffusion_pytorch_model.bin" goto sd_already

echo  µÚ 2 ²½: µ÷ÓÃ Python ²¢·¢ÏÂÔØÆ÷
echo  µÚÒ»´Î»áÁÙÊ±°²×° modelscope + huggingface_hub (Çå»ªÔ´, ~15s)...
echo.
python -c "import modelscope, huggingface_hub" >nul 2>&1
if errorlevel 1 python -m pip install modelscope huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple

echo  ¿ªÊ¼²¢·¢ÏÂÔØ(4 Ïß³Ì + ¶ÏµãĞø´«)...
echo  Ô¤¼ÆºÄÊ±(¹úÄÚÍøÂç): 30 Mbps ¡ú Ô¼ 15-20 ·ÖÖÓ
echo.
python "%~dp0_download_sd.py"
goto sd_done

:sd_already
echo  ¼ì²âµ½ SD Ä£ĞÍÒÑÏÂÔØ,Ìø¹ı
echo  ÈçĞèÖØĞÂÏÂÔØ,ÇëÉ¾³ı models\sd\runwayml_stable-diffusion-v1-5 Õû¸öÄ¿Â¼ºóÖØÅÜ
echo.

:sd_done
echo.
echo  ½ÓÏÂÀ´:
echo    1. Ë«»÷¸ùÄ¿Â¼ [Ò»¼üÔËĞĞ.bat] Æô¶¯ÔÆÖÇ
echo    2. ½øÈë [»­Í¼] Ò³ÃæÊÔ³öÍ¼
echo    3. Ñ¡Ôñ¡¸²å»­¡¹ÀàĞÍ,SD Ä£ĞÍ¼´¿ÉÉúĞ§

echo.
pause
exit /b
