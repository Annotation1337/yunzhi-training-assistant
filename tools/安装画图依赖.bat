@echo off
chcp 936 >nul
title ÔÆÖÇ - °²×°»­Í¼ÒÀÀµ(PyTorch + diffusers)
cd /d "%~dp0.."

echo [95m==============================================[0m
echo [95m     ÔÆÖÇ - °²×°»­Í¼ÒÀÀµ(PyTorch + diffusers)[0m
echo [95m==============================================[0m
echo.
echo  ÓÃÍ¾: °²×°¡¸²å»­¡¹³öÍ¼ËùĞèµÄ PyTorch + diffusers È«¼ÒÍ°
echo  ËµÃ÷: ÍØÆË/¼Ü¹¹Í¼ÓÃ matplotlib,ÒÑÔÚ»ù´¡ÒÀÀµÀï°²×°
echo        ±¾½Å±¾²¹ÆëµÄÊÇ¡¸²å»­¡¹ÓÃ Stable Diffusion µÄÍÆÀíÒÀÀµ
echo  ´óĞ¡: Ô¼ 2-3 GB (PyTorch ½Ï´ó,ÇëÁô×ã´ÅÅÌ)
echo  À´Ô´: Çå»ª¾µÏñÔ´,¹úÄÚËÙ¶È¿ì
echo.

echo  µÚ 1 ²½: ¼ì²é Python
python --version >nul 2>&1
if errorlevel 1 goto dd_no_py
python --version

echo  µÚ 2 ²½: ¼ì²âÏÔ¿¨(¾ö¶¨×° CPU °æ»¹ÊÇ GPU °æ)
where nvidia-smi >nul 2>&1
if errorlevel 1 goto dd_cpu
nvidia-smi >nul 2>&1
if errorlevel 1 goto dd_cpu
echo  ¼ì²âµ½ NVIDIA ÏÔ¿¨,½«°²×° GPU °æ PyTorch (CUDA 12.1)
echo.
echo  ÕıÔÚ°²×° torch / torchvision [GPU °æ,Ô¼ 2.5GB]...
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 goto dd_gpu_fallback
goto dd_rest

:dd_gpu_fallback
echo  ¾¯¸æ: GPU °æ°²×°Ê§°Ü(¿ÉÄÜÊÇÍøÂç»òÇı¶¯),¸ÄÓÃÇå»ªÔ´ CPU °æ...
goto dd_cpu

:dd_cpu
echo  Î´¼ì²âµ½¿ÉÓÃ NVIDIA ÏÔ¿¨,°²×° CPU °æ PyTorch(³öÍ¼½ÏÂıµ«¿ÉÓÃ)
echo.
echo  ÕıÔÚ°²×° torch / torchvision [CPU °æ,Ô¼ 200MB]...
python -m pip install torch torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 goto dd_fail

:dd_rest
echo.
echo  ÕıÔÚ°²×° diffusers / transformers / accelerate / safetensors ...
python -m pip install modelscope diffusers transformers accelerate safetensors huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 goto dd_fail

echo.
echo  µÚ 3 ²½: ÑéÖ¤°²×°½á¹û
python -c "import torch, diffusers; print('  torch:', torch.__version__); print('  diffusers:', diffusers.__version__); print('  CUDA', torch.cuda.is_available())"
if errorlevel 1 goto dd_fail

echo.
echo  ==============================================
echo   °²×°³É¹¦! »­Í¼ÒÀÀµÒÑ¾ÍĞ÷
echo  ==============================================
echo   ÏÂÒ»²½:
echo     1. ¹Ø±Õ²¢ÖØĞÂË«»÷ Ò»¼üÔËĞĞ.bat Æô¶¯ÔÆÖÇ
echo     2. ½øÈë¡¸»­Í¼¡¹Ò³ÃæÑ¡Ôñ¡¸²å»­¡¹ÀàĞÍ¼´¿ÉÉúĞ§
echo     3. ÈôÉĞÎ´ÏÂÔØ SD Ä£ĞÍ,ÏÈÔËĞĞ tools\ÏÂÔØStableDiffusion.bat
goto dd_end

:dd_no_py
echo  ´íÎó: Î´¼ì²âµ½ Python,ÇëÏÈÔËĞĞ tools\°²×°Python.bat
goto dd_end

:dd_fail
echo  ´íÎó: ÒÀÀµ°²×°Ê§°Ü
echo  ÅÅ²é½¨Òé:
echo    1. ¼ì²éÍøÂçÊÇ·ñ¿É·ÃÎÊ pypi.tuna.tsinghua.edu.cn
echo    2. ¼ì²é´ÅÅÌÊ£Óà¿Õ¼äÊÇ·ñ´óÓÚ 5GB
echo    3. ÊÖ¶¯Ö´ĞĞ:
echo       python -m pip install modelscope torch diffusers transformers accelerate safetensors
echo       -i https://pypi.tuna.tsinghua.edu.cn/simple

:dd_end

echo.
pause
exit /b
