@echo off
chcp 936 >nul
title тфжг - обтьдёпм м╗рЕг╖нй Qwen2.5  7B
cd /d "%~dp0.."

echo [95m==============================================[0m
echo [95m     тфжг - обтьдёпм м╗рЕг╖нй Qwen2.5  7B[0m
echo [95m==============================================[0m
echo.
echo  дёпм: м╗рЕг╖нй Qwen2.5  7B
echo  ╠Йг╘: qwen2.5:7b
echo  ╢Сп║: т╪ 4.7 GB
echo  к╣цВ: ╟╒юОм╗рЕг╖нй 70 рз╡нйЩ╬Ы╨Б╟Ф
echo  Ё║╬╟: ╦╢тсмфюМ  мф╪Ж 8GB дз╢Ф ╩Р 6GB от╢Ф
echo.
echo  обтьт╢╡ъбт:
echo    1. ╧Здзт╢ modelscope.cn (╟╒юОтф, мф╪Ж╧Здз╩╥╬Ё)
echo    2. Ollama ╧ы╥╫ registry (╬ЁмБ, е╪╤Ш╡╩нх)
echo    3. хТа╫╦Ж╤╪й╖╟э,╦ЬЁЖйж╤╞╫лЁл
echo.

echo  ╣з 1 ╡╫: ╪Л╡И Ollama ╥ЧнЯ
where ollama >nul 2>&1
if errorlevel 1 goto no_ollama
curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto ollama_offline
echo  Ollama тзоъ
echo.

echo  ╣з 2 ╡╫: ╪Л╡Идёпмйг╥Яря╢Фтз
ollama list | findstr /I "qwen2.5:7b" >nul 2>&1
if not errorlevel 1 goto already_exists

echo  ╣з 3 ╡╫: ©╙й╪обтьдёпм
echo  уЩтзю╜х║ qwen2.5:7b,йв╢нпХобть т╪ 4.7 GB
echo  х║╬ЖсзмЬкы,т╪пХ 3-20 ╥жжс
echo  обть╧ЩЁлжпгКнП╧ь╠у╢к╢╟©з
echo.
ollama pull qwen2.5:7b
if errorlevel 1 goto pull_fail
echo.
echo  обтьмЙЁи
echo.

echo  яИж╓дёпмйг╥Я╟╡в╟Ёи╧╕
ollama list | findstr /I "qwen2.5:7b" >nul 2>&1
if errorlevel 1 goto verify_fail
echo  дёпмря╬мпВ
echo.
echo ==============================================
echo   м╗рЕг╖нй Qwen2.5  7B  ╟╡в╟Ёи╧╕
echo ==============================================
echo.
echo  ╫собю╢:
echo    1. к╚╩В╦Ыд©б╪ [р╩╪Эткпп.bat] фТ╤╞тфжг
echo    2. Д╞ююфВ╥цнй http://localhost:5000
echo    3. ╦цдёпм╩Авт╤╞╠╩╣Всц
echo.

:already_exists
echo  ╦цдёпмря╢Фтз,нчпХжь╦╢обть
echo  хГпХжьв╟,гКохж╢пп ollama rm qwen2.5:7b
echo.

:no_ollama
echo.
echo  ╢МнС: н╢╪Л╡Б╣╫ Ollama
echo  гКохткпп tools\╟╡в╟Ollama.bat ╟╡в╟╥ЧнЯ
echo.

:ollama_offline
echo.
echo  ╢МнС: Ollama ╥ЧнЯн╢ткпп
echo  гК╢Р©╙©╙й╪╡к╣╔ - кякВ Ollama - фТ╤╞╥ЧнЯ
echo  ╥ЧнЯфТ╤╞╨Стыткпп╢к bat
echo.

:pull_fail
echo.
echo  ╢МнС: дёпмобтьй╖╟э
echo  ©идэт╜рР:
echo    1. мЬбГ╡╩нх╤╗,Ollama д╛хо╡ж©Бтз╬ЁмБ
echo    2. ╢еел©у╪Д╡╩вЦ,пХжаиы 5GB ©исц©у╪Д
echo    3. Ollama ╥ЧнЯрЛЁё,гКжьфТ Ollama ╨Сжьйт
echo.
echo  ╫Б╬Ж╥╫╟╦ (╟╢мф╪ЖкЁпР):
echo    ╥╫╥╗ 1: жьйт╠╬ bat (мЬбГе╪╤Ш╤╤╤╞,╤Ю╟К╧эсц)
echo    ╥╫╥╗ 2: ит╣х╪╦╥жжстыйт,╠э©╙мЬбГ╦ъ╥Е
echo    ╥╫╥╗ 3: ╪Л╡ИмЬбГ╢ЗюМ/╥ю╩Пг╫йг╥Яю╧╫ьак ollama.com
echo    ╥╫╥╗ 4: ╩╩╦Жп║дёпм [хГ deepseek-r1:1.5b ╫Ж 1.1GB],тыткпп╠╬ bat
echo    ╥╫╥╗ 5: йж╤╞обть GGUF ╨С╣╪хК
echo      1. ╥цнй https://modelscope.cn (╟╒юОтф,╧Здз©и╥цнй)
echo      2. кякВ╡╒обть╤тс╕ .gguf нд╪Ч
echo      3. пб╫╗ Modelfile п╢хК: FROM ./дЦ╣днд╪Ч.gguf
echo      4. ж╢пп: ollama create my-model -f Modelfile
echo      5. иХжц╩╥╬Ё╠Да©: set OLLAMA_MODEL=my-model
echo.
echo  лАй╬: дёпм╢Ф╥етз %USERPROFILE%\.ollama\models [Ollama ╧ы╥╫т╪╤╗,нП╦д]

:verify_fail
echo.
echo  ╢МнС: дёпмяИж╓й╖╟э
echo  гКж╢пп ollama list ╡И©╢ря╟╡в╟дёпм
echo.

echo.
pause
exit /b
