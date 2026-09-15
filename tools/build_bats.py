# -*- coding: utf-8 -*-
"""
云智实训助手 · Windows bat 工具集生成器
======================================
生成 bat 脚本（普通用户只接触根目录的 一键运行.bat）：

    根目录/
        一键运行.bat        - 唯一入口：环境检测 + 缺啥补啥 + 启动
    tools/                  - 其余脚本全部收纳在此
        一键安装.bat        - 交互式安装向导（必选自动 + 可选菜单）
        安装Python.bat      - 单独装 Python
        安装Ollama.bat      - 单独装 Ollama
        下载StableDiffusion.bat - 单独下载 SD 模型（约 4GB，国内源优先）
        安装模型_xxx.bat    - 单独下载模型 x6
        启动.bat            - 仅启动（由用户手动维护）

为什么用 Python 生成 bat：
    - 严格保证 GBK + CRLF 编码（之前发现 Edit 工具会破坏 GBK）
    - 避开全角括号「（）」和 for /f 解析陷阱
    - 模板统一管理，方便后续增删

运行：
    python3 build_bats.py
"""

import os

# build_bats.py 位于 tools/ 下
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # tools/
ROOT_DIR = os.path.dirname(BASE_DIR)                            # 项目根目录


# ============================================================
# bat 通用约束（已踩坑）
# ============================================================
# 1. 文件编码必须是 GBK + CRLF（Windows cmd 才能正确显示中文）
# 2. echo 内容里禁止出现全角括号「（）」，会触发"此时不应有"
# 3. 禁止使用 for /f "tokens=* delims=..." 解析带特殊字符的输出
# 4. 标签用半角冒号 :no_python，goto 不跨标签


def write_bat(name, lines, root=False):
    """写入 GBK + CRLF 编码的 bat 文件
    root=True 写到项目根目录，否则写到 tools/"""
    base = ROOT_DIR if root else BASE_DIR
    path = os.path.join(base, name)
    content = "\r\n".join(lines) + "\r\n"
    with open(path, "wb") as f:
        f.write(content.encode("gbk"))
    where = "根目录" if root else "tools/"
    print(f"已生成: {where}{name}  ({len(content)} 字节)")


def header(title, up=False):
    """统一输出头部；up=True 时 cd 到上级目录（tools/ 下的脚本要回项目根运行）

    颜色策略：Windows 10+ 的 cmd 原生支持 ANSI 转义。
    直接把 ESC 字符(\\x1b)写进 bat 文件即可（GBK 编码下 ESC 是单字节 0x1B，无冲突）。
    仅给「关键字段」上色，普通说明文字保持默认色，避免花哨刺眼。
    """
    cd = 'cd /d "%~dp0.."' if up else "cd /d %~dp0"
    E = "\x1b"  # ESC
    return [
        "@echo off",
        "chcp 936 >nul",
        "title " + title,
        cd,
        "",
        f"echo {E}[95m=============================================={E}[0m",
        f"echo {E}[95m     {title}{E}[0m",
        f"echo {E}[95m=============================================={E}[0m",
        "echo.",
    ]


# ---------- 彩色文本辅助（仅在需要处调用，普通文字不上色）----------
_C = {
    "ok":    "\x1b[92m",   # 亮绿：成功/就绪
    "warn":  "\x1b[93m",   # 亮黄：警告/未启用
    "err":   "\x1b[91m",   # 亮红：错误
    "info":  "\x1b[96m",   # 亮青：信息/路径
    "val":   "\x1b[93m",   # 亮黄：关键值（模型名/版本号）
    "reset": "\x1b[0m",
}


def c(text, kind):
    """给一段文字加 ANSI 颜色（kind: ok/warn/err/info/val）"""
    return f"{_C.get(kind,'')}{text}{_C['reset']}"


def footer_pause():
    return ["", "echo.", "pause", "exit /b"]


# ============================================================
# 1. 安装Ollama.bat
# ============================================================
def build_install_ollama():
    """生成 安装Ollama.bat

    下载策略：
        1. 优先用 curl.exe（Win10 1803+ 自带）直接下载 OllamaSetup.exe
        2. 失败时回退到 PowerShell
        3. 都不行提示手动下载
    """
    lines = header("云智实训助手 - 安装 Ollama 本地大模型服务", up=True)

    lines += [
        "echo  首次安装约需 5-10 分钟 [下载约 200MB]",
        "echo  适用于 Windows 10 / 11 x64",
        "echo  下载源: ollama.com 原版 [直接下载]",
        "echo  若失败: 尝试 PowerShell, 再失败则提示手动下载",
        "echo.",
        "",
        "echo  第 1 步: 检查 Ollama 是否已安装",
        "where ollama >nul 2>&1",
        "if not errorlevel 1 goto already_installed",
        "",
"echo  第 2 步: 下载 Ollama 安装包 [来源 ollama.com 原版]",
        "echo  下载中,请稍候...",
        "echo.",
        "if exist ollama-installer.exe goto skip_download",
        "",
        "curl -L --retry 3 --retry-delay 5 -C - -o ollama-installer.exe --connect-timeout 15 --max-time 3600 https://ollama.com/download/OllamaSetup.exe",
        "if not errorlevel 1 goto skip_download",
        "echo  curl 失败,尝试 PowerShell...",
        "del ollama-installer.exe >nul 2>&1",
        "powershell -NoProfile -ExecutionPolicy Bypass -Command try { Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'ollama-installer.exe' -UseBasicParsing } catch { exit 1 }",
        "if not errorlevel 1 goto skip_download",
        "del ollama-installer.exe >nul 2>&1",
        "goto download_fail",
        "",
        ":skip_download",
        "if not exist ollama-installer.exe goto download_fail",
        "echo  下载完成",
        "echo.",
        "",
        "echo  第 3 步: 静默安装 Ollama",
        "echo  正在安装,请稍候,可能弹出 UAC 确认...",
        "ollama-installer.exe /S",
        "if errorlevel 1 goto install_fail",
        "echo  安装完成",
        "echo.",
        "del ollama-installer.exe >nul 2>&1",
        "",
        "echo  第 4 步: 启动 Ollama 服务",
        "echo  Ollama 安装后会自动后台运行,无需手动启动",
        "echo  如未启动,请在开始菜单搜索 Ollama 并打开",
        "echo.",
        "echo  等待服务就绪,约 5-15 秒...",
        "ping -n 10 127.0.0.1 >nul",
        "",
        "echo  验证 Ollama 是否在线",
        "curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1",
        "if errorlevel 1 goto ollama_not_running",
        "echo  Ollama 服务已就绪",
        "echo.",
        "echo ==============================================",
        "echo   Ollama 安装成功",
        "echo   下一步: 双击根目录 [一键运行.bat] 即可使用",
        "echo   也可运行 tools\\安装模型_xxx.bat 单独下载模型",
        "echo ==============================================",
        "echo.",
        "",
        ":already_installed",
        "echo  检测到 Ollama 已安装",
        "ollama --version",
        "echo.",
        "echo  验证 Ollama 服务...",
        "curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1",
        "if not errorlevel 1 goto ollama_running",
        "echo  警告: Ollama 已装但服务未运行",
        "echo  请打开开始菜单 - Ollama 启动服务",
        "echo.",
        "pause",
        "exit /b",
        "",
        ":ollama_running",
        "echo  Ollama 服务在线,无需重复安装",
        "echo  可运行 tools\\安装模型_xxx.bat 下载更多模型",
        "echo.",
        "pause",
        "exit /b",
        "",
        ":download_fail",
        "echo.",
        "echo  错误: Ollama 下载失败 (ollama.com + PowerShell 都失败)",
        "echo  可能原因: 网络不通,或被防火墙拦截",
        "echo.",
        "if exist ollama-installer.exe (",
        "    echo  检测到半成品 ollama-installer.exe",
        "    dir ollama-installer.exe | findstr ollama-installer",
        ")",
        "echo.",
        "echo  解决方案 (按推荐顺序):",
        "echo    1. 重跑本 bat [本脚本会从断点续传 -C - 自动续下未完成部分]",
        "echo    2. 浏览器访问 https://ollama.com/download 下载 OllamaSetup.exe",
        "echo    3. 把下载的 OllamaSetup.exe 放到本 bat 所在目录",
        "echo    4. 重命名为 ollama-installer.exe 后再运行此 bat",
        "echo.",
        "echo  进阶: PowerShell 手动续传命令 (在 bat 所在目录运行):",
        "echo    powershell -Command \"(New-Object Net.WebClient).DownloadFile('https://ollama.com/download/OllamaSetup.exe','ollama-installer.exe')\"",
        "echo.",
        "echo  模型 (qwen2.5:3b 等) 下载也会用同样的策略 (ollama 官方源)",
        "echo  如仍有问题,可联系管理员协助",
        "echo.",
        "pause",
        "exit /b",
        "",
        ":install_fail",
        "echo.",
        "echo  错误: 安装失败",
        "echo  请右键 [此 bat] - 以管理员身份运行",
        "echo.",
        "del ollama-installer.exe >nul 2>&1",
        "pause",
        "exit /b",
        "",
        ":ollama_not_running",
        "echo.",
        "echo  警告: Ollama 已安装但服务未启动",
        "echo  请打开开始菜单 - 搜索 Ollama - 点击运行",
        "echo  启动后再次运行此 bat 验证",
        "echo.",
    ]

    lines += footer_pause()
    write_bat("安装Ollama.bat", lines)


# ============================================================
# 2. 安装模型_xxx.bat 模板
# ============================================================
# 国产大模型清单（精选 6 个，覆盖不同场景）
MODELS = [
    {
        "id": "qwen3b",
        "name": "通义千问 Qwen2.5  3B",
        "tag": "qwen2.5:3b",
        "size": "约 2.0 GB",
        "desc": "阿里通义千问 30 亿参数轻量版",
        "use": "日常问答  推荐 4GB 内存",
    },
    {
        "id": "qwen7b",
        "name": "通义千问 Qwen2.5  7B",
        "tag": "qwen2.5:7b",
        "size": "约 4.7 GB",
        "desc": "阿里通义千问 70 亿参数均衡版",
        "use": "复杂推理  推荐 8GB 内存 或 6GB 显存",
    },
    {
        "id": "deepseek15b",
        "name": "DeepSeek R1  1.5B",
        "tag": "deepseek-r1:1.5b",
        "size": "约 1.1 GB",
        "desc": "深度求索推理模型  轻量版",
        "use": "数学推理  推荐 4GB 内存",
    },
    {
        "id": "glm4",
        "name": "智谱 GLM4  9B",
        "tag": "glm4:9b",
        "size": "约 5.5 GB",
        "desc": "智谱清言  工具调用能力强",
        "use": "工具调用  推荐 8GB 内存 或 6GB 显存",
    },
    {
        "id": "yi6b",
        "name": "零一万物 Yi  6B",
        "tag": "yi:6b",
        "size": "约 3.8 GB",
        "desc": "李开复零一万物  中英文均衡",
        "use": "通用对话  推荐 6GB 内存",
    },
    {
        "id": "qwenCoder7b",
        "name": "通义千问 Qwen2.5-Coder  7B",
        "tag": "qwen2.5-coder:7b",
        "size": "约 4.7 GB",
        "desc": "阿里代码专用模型",
        "use": "代码生成  推荐 8GB 内存 或 6GB 显存",
    },
]


def build_install_model(m):
    """生成单个模型安装 bat

    核心逻辑：
        1. 检查 ollama 命令是否存在
        2. 检查 Ollama 服务是否在线
        3. 检查模型是否已存在
        4. ollama pull 拉取模型
        5. 验证安装
    """
    title = f"云智 - 下载模型 {m['name']}"
    fname = f"安装模型_{m['id']}.bat"

    lines = header(title, up=True)
    lines += [
        f"echo  模型: {m['name']}",
        f"echo  标签: {m['tag']}",
        f"echo  大小: {m['size']}",
        f"echo  说明: {m['desc']}",
        f"echo  场景: {m['use']}",
        "echo.",
        "echo  下载源策略:",
        "echo    1. 国内源 modelscope.cn (阿里云, 推荐国内环境)",
        "echo    2. Ollama 官方 registry (境外, 偶尔不稳)",
        "echo    3. 若两个都失败,给出手动教程",
        "echo.",
        "",
        "echo  第 1 步: 检查 Ollama 服务",
        "where ollama >nul 2>&1",
        "if errorlevel 1 goto no_ollama",
        "curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1",
        "if errorlevel 1 goto ollama_offline",
        "echo  Ollama 在线",
        "echo.",
        "",
        "echo  第 2 步: 检查模型是否已存在",
        f"ollama list | findstr /I \"{m['tag']}\" >nul 2>&1",
        "if not errorlevel 1 goto already_exists",
        "",
        "echo  第 3 步: 开始下载模型",
        f"echo  正在拉取 {m['tag']},首次需下载 {m['size']}",
        "echo  取决于网速,约需 3-20 分钟",
        "echo  下载过程中请勿关闭此窗口",
        "echo.",
        f"ollama pull {m['tag']}",
        "if errorlevel 1 goto pull_fail",
        "echo.",
        "echo  下载完成",
        "echo.",
        "",
        "echo  验证模型是否安装成功",
        f"ollama list | findstr /I \"{m['tag']}\" >nul 2>&1",
        "if errorlevel 1 goto verify_fail",
        "echo  模型已就绪",
        "echo.",
        "echo ==============================================",
        f"echo   {m['name']}  安装成功",
        "echo ==============================================",
        "echo.",
        "echo  接下来:",
        "echo    1. 双击根目录 [一键运行.bat] 启动云智",
        "echo    2. 浏览器访问 http://localhost:5000",
        "echo    3. 该模型会自动被调用",
        "echo.",
        "",
        ":already_exists",
        "echo  该模型已存在,无需重复下载",
        f"echo  如需重装,请先执行 ollama rm {m['tag']}",
        "echo.",
        "",
        ":no_ollama",
        "echo.",
        "echo  错误: 未检测到 Ollama",
        "echo  请先运行 tools\\安装Ollama.bat 安装服务",
        "echo.",
        "",
        ":ollama_offline",
        "echo.",
        "echo  错误: Ollama 服务未运行",
        "echo  请打开开始菜单 - 搜索 Ollama - 启动服务",
        "echo  服务启动后再运行此 bat",
        "echo.",
        "",
        ":pull_fail",
        "echo.",
        "echo  错误: 模型下载失败",
        "echo  可能原因:",
        "echo    1. 网络不稳定,Ollama 默认仓库在境外",
        "echo    2. 磁盘空间不足,需至少 5GB 可用空间",
        "echo    3. Ollama 服务异常,请重启 Ollama 后重试",
        "echo.",
        "echo  解决方案 (按推荐顺序):",
        "echo    方法 1: 重试本 bat (网络偶尔抖动,多半管用)",
        "echo    方法 2: 稍等几分钟再试,避开网络高峰",
        "echo    方法 3: 检查网络代理/防火墙是否拦截了 ollama.com",
        "echo    方法 4: 换个小模型 [如 deepseek-r1:1.5b 仅 1.1GB],再运行本 bat",
        "echo    方法 5: 手动下载 GGUF 后导入",
        "echo      1. 访问 https://modelscope.cn (阿里云,国内可访问)",
        "echo      2. 搜索并下载对应 .gguf 文件",
        "echo      3. 新建 Modelfile 写入: FROM ./你的文件.gguf",
        "echo      4. 执行: ollama create my-model -f Modelfile",
        "echo      5. 设置环境变量: set OLLAMA_MODEL=my-model",
        "echo.",
        "echo  提示: 模型存放在 %USERPROFILE%\\.ollama\\models [Ollama 官方约定,勿改]",
        "",
        ":verify_fail",
        "echo.",
        "echo  错误: 模型验证失败",
        "echo  请执行 ollama list 查看已安装模型",
        "echo.",
    ]

    lines += footer_pause()
    write_bat(fname, lines)


# ============================================================
# 2.5 tools/安装Python.bat（单独安装，逻辑与一键运行内嵌一致）
# ============================================================
def build_install_python():
    title = "云智实训助手 - Python 安装程序"
    lines = header(title, up=True)
    lines += [
        "python --version >nul 2>&1",
        "if errorlevel 1 goto need_install",
        "python --version",
        "echo  Python 已安装,无需重复安装",
        "echo  双击根目录 [一键运行.bat] 即可使用",
    ] + footer_pause()
    lines += [
        "",
        ":need_install",
        "echo  未检测到 Python,开始自动安装...",
        "where winget >nul 2>&1",
        "if errorlevel 1 goto use_curl",
        "winget install Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements",
        "if not errorlevel 1 goto refresh",
        "",
        ":use_curl",
        'set "PYEXE=%TEMP%\\yunzhi_py\\python-3.11.9-amd64.exe"',
        'if not exist "%TEMP%\\yunzhi_py" mkdir "%TEMP%\\yunzhi_py"',
        "curl -L -o \"%PYEXE%\" \"https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-amd64.exe\" --connect-timeout 30",
        'if exist "%PYEXE%" goto install',
        "curl -L -o \"%PYEXE%\" \"https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe\" --connect-timeout 30",
        'if exist "%PYEXE%" goto install',
        "echo  下载失败,请手动安装: https://www.python.org/downloads/",
        "echo  务必勾选 Add Python to PATH",
    ] + footer_pause()
    lines += [
        "",
        ":install",
        'if exist "%PYEXE%" "%PYEXE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0',
        "",
        ":refresh",
        'set "PATH=%PATH%;%LOCALAPPDATA%\\Programs\\Python\\Python311;%LOCALAPPDATA%\\Programs\\Python\\Python311\\Scripts"',
        "python --version >nul 2>&1",
        "if errorlevel 1 goto path_warn",
        "python --version",
        "echo  安装成功! 双击根目录 [一键运行.bat] 即可使用",
    ] + footer_pause()
    lines += [
        "",
        ":path_warn",
        "echo  已安装但当前窗口未识别,请关闭窗口后重新双击本文件",
    ] + footer_pause()
    write_bat("安装Python.bat", lines)


# ============================================================
# 2.55 tools/下载StableDiffusion.bat —— Python 并发下载（10倍速）
# ============================================================
def build_download_sd():
    title = "云智 - 下载 Stable Diffusion 模型(智能加速版)"
    lines = header(title, up=True)
    lines += [
        "echo  模型: runwayml/stable-diffusion-v1-5 (标准版 ~3.2GB)",
        "echo  用途: 本地 AI 出图(拓扑图仍可用 matplotlib)",
        "echo  存放位置: %CD%\\models\\sd\\runwayml_stable-diffusion-v1-5",
        "echo.",
        "echo  加速策略(三级回退,国内环境稳如狗):",
        "echo    1. ModelScope 官方镜像 (阿里云 CDN,首选,最快最稳)",
        "echo    2. hf-mirror.com 国内 HF 镜像 (回退)",
        "echo    3. huggingface.co 原版 (最后兜底,国内多不通)",
        "echo    4. Python 4 线程并发 + 断点续传(比 curl 快 5-10x)",
        "echo    5. 智能重试:单文件超时自动续传,不全重来",
        "echo    6. 已下载文件自动跳过",
        "echo.",
        "",
        "echo  第 1 步: 检查是否已下载",
        'if exist "%CD%\\models\\sd\\runwayml_stable-diffusion-v1-5\\unet\\diffusion_pytorch_model.bin" goto sd_already',
        "",
        "echo  第 2 步: 调用 Python 并发下载器",
        "echo  第一次会临时安装 modelscope + huggingface_hub (清华源, ~15s)...",
        "echo.",
        "python -c \"import modelscope, huggingface_hub\" >nul 2>&1",
        "if errorlevel 1 python -m pip install modelscope huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "",
        "echo  开始并发下载(4 线程 + 断点续传)...",
        "echo  预计耗时(国内网络): 30 Mbps → 约 15-20 分钟",
        "echo.",
        'python "%~dp0_download_sd.py"',
        "goto sd_done",
        "",
        ":sd_already",
        "echo  检测到 SD 模型已下载,跳过",
        "echo  如需重新下载,请删除 models\\sd\\runwayml_stable-diffusion-v1-5 整个目录后重跑",
        "echo.",
        "",
        ":sd_done",
        "echo.",
        "echo  接下来:",
        "echo    1. 双击根目录 [一键运行.bat] 启动云智",
        "echo    2. 进入 [画图] 页面试出图",
        "echo    3. 选择「插画」类型,SD 模型即可生效",
    ] + footer_pause()

    write_bat("下载StableDiffusion.bat", lines)


# ============================================================
# 2.56 tools/安装画图依赖.bat —— 一键补装 PyTorch + diffusers
# ============================================================
# 2.56 tools/安装画图依赖.bat —— 一键补装 PyTorch + diffusers
# ============================================================
def build_install_draw_deps():
    title = "云智 - 安装画图依赖(PyTorch + diffusers)"
    lines = header(title, up=True)
    lines += [
        "echo  用途: 安装「插画」出图所需的 PyTorch + diffusers 全家桶",
        "echo  说明: 拓扑/架构图用 matplotlib,已在基础依赖里安装",
        "echo        本脚本补齐的是「插画」用 Stable Diffusion 的推理依赖",
        "echo  大小: 约 2-3 GB (PyTorch 较大,请留足磁盘)",
        "echo  来源: 清华镜像源,国内速度快",
        "echo.",
        "",
        "echo  第 1 步: 检查 Python",
        "python --version >nul 2>&1",
        "if errorlevel 1 goto dd_no_py",
        "python --version",
        "",
        "echo  第 2 步: 检测显卡(决定装 CPU 版还是 GPU 版)",
        "where nvidia-smi >nul 2>&1",
        "if errorlevel 1 goto dd_cpu",
        "nvidia-smi >nul 2>&1",
        "if errorlevel 1 goto dd_cpu",
        "echo  检测到 NVIDIA 显卡,将安装 GPU 版 PyTorch (CUDA 12.1)",
        "echo.",
        "echo  正在安装 torch / torchvision [GPU 版,约 2.5GB]...",
        "python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121",
        "if errorlevel 1 goto dd_gpu_fallback",
        "goto dd_rest",
        "",
        ":dd_gpu_fallback",
        "echo  警告: GPU 版安装失败(可能是网络或驱动),改用清华源 CPU 版...",
        "goto dd_cpu",
        "",
        ":dd_cpu",
        "echo  未检测到可用 NVIDIA 显卡,安装 CPU 版 PyTorch(出图较慢但可用)",
        "echo.",
        "echo  正在安装 torch / torchvision [CPU 版,约 200MB]...",
        "python -m pip install torch torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "if errorlevel 1 goto dd_fail",
        "",
        ":dd_rest",
        "echo.",
        "echo  正在安装 diffusers / transformers / accelerate / safetensors ...",
        "python -m pip install modelscope diffusers transformers accelerate safetensors huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "if errorlevel 1 goto dd_fail",
        "",
        "echo.",
        "echo  第 3 步: 验证安装结果",
        'python -c "import torch, diffusers; print(\'  torch:\', torch.__version__); print(\'  diffusers:\', diffusers.__version__); print(\'  CUDA\', torch.cuda.is_available())"',
        "if errorlevel 1 goto dd_fail",
        "",
        "echo.",
        "echo  ==============================================",
        "echo   安装成功! 画图依赖已就绪",
        "echo  ==============================================",
        "echo   下一步:",
        "echo     1. 关闭并重新双击 一键运行.bat 启动云智",
        "echo     2. 进入「画图」页面选择「插画」类型即可生效",
        "echo     3. 若尚未下载 SD 模型,先运行 tools\\下载StableDiffusion.bat",
        "goto dd_end",
        "",
        ":dd_no_py",
        "echo  错误: 未检测到 Python,请先运行 tools\\安装Python.bat",
        "goto dd_end",
        "",
        ":dd_fail",
        "echo  错误: 依赖安装失败",
        "echo  排查建议:",
        "echo    1. 检查网络是否可访问 pypi.tuna.tsinghua.edu.cn",
        "echo    2. 检查磁盘剩余空间是否大于 5GB",
        "echo    3. 手动执行:",
        "echo       python -m pip install modelscope torch diffusers transformers accelerate safetensors",
        "echo       -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "",
        ":dd_end",
    ] + footer_pause()

    write_bat("安装画图依赖.bat", lines)


# ============================================================
# 2.58 tools/安装OCR依赖.bat —— 一键补装 pytesseract (Python 包)
# ============================================================
# 注意：Tesseract 程序本体需另行从 GitHub 下载（非 pip 可装）
def build_install_ocr():
    title = "云智实训助手 - 安装 OCR 截图识别依赖"
    lines = header(title) + [
        "echo  用途: 排错诊断页面的「截图识别」功能",
        "echo  说明: 本脚本只装 Python 包 pytesseract;",
        "echo        Tesseract 程序本体需另行下载(约 60MB)",
        "echo  预计耗时: 约 10-30 秒",
        "echo.",
        "echo  第 1 步: 检测 Python",
        "python --version >nul 2>&1",
        "if errorlevel 1 goto od_no_py",
        "python --version",
        "echo.",
        "echo  第 2 步: 安装 pytesseract (清华源)",
        "python -m pip install pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "if errorlevel 1 python -m pip install pytesseract",
        "echo.",
        "echo  第 3 步: 验证",
        'python -c "import pytesseract; print(\'  pytesseract:\', pytesseract.__version__)"',
        "if errorlevel 1 goto od_fail",
        "echo.",
        "echo  ==============================================",
        "echo   pytesseract 装好了!",
        "echo  ==============================================",
        "echo  下一步:",
        "echo    1. 装 Tesseract 程序本体 (Windows 用户):",
        "echo       https://github.com/UB-Mannheim/tesseract/wiki",
        "echo       下载 tesseract-ocr-w64-setup-xxx.exe 安装",
        "echo       安装时勾选「简体中文」语言包",
        "echo    2. 或用 winget 一行命令:",
        "echo       winget install tesseract-ocr.tesseract",
        "echo    3. 重启 云智 后,排错诊断页面的截图识别即可生效",
        "echo.",
        "echo  如果不装 Tesseract 程序,云智其他功能(知识库/联网/画拓扑图)完全正常",
        "goto od_end",
        "",
        ":od_no_py",
        "echo  错误: 未检测到 Python,请先运行 tools\\安装Python.bat",
        "goto od_end",
        "",
        ":od_fail",
        "echo  错误: pytesseract 安装失败,请检查网络后重试",
        "echo  手动命令:",
        "echo    python -m pip install pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "",
        ":od_end",
    ] + footer_pause()

    write_bat("安装OCR依赖.bat", lines)


# ============================================================
# 2.565 tools/安装语音识别.bat —— 装 vosk 库 + 中文模型（本地离线 ASR）
# ============================================================
def build_install_asr():
    title = "云智实训助手 - 安装语音识别组件(本地离线)"
    lines = header(title, up=True)
    lines += [
        "echo  用途: 智能问答页的「麦克风语音输入」功能",
        "echo  说明: 采用本地离线识别引擎 Vosk,音频不上传任何外部服务器",
        "echo  组成: vosk 库 [约 3MB] + 中文模型 [约 42MB]",
        "echo  预计耗时: 约 1-3 分钟 [清华源 + 国内镜像]",
        "echo.",
        "echo  数据本地化承诺:",
        "echo    录音只在浏览器采集,送本机 127.0.0.1 识别,识别后立即删除,",
        "echo    全程不联网、不外发,符合学校数据安全要求。",
        "echo.",
        "",
        "echo  第 1 步: 检测 Python",
        "python --version >nul 2>&1",
        "if errorlevel 1 goto asr_no_py",
        "python --version",
        "echo.",
        "echo  第 2 步: 安装 vosk 库 [清华源]",
        "python -m pip install vosk -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "if errorlevel 1 python -m pip install vosk",
        'python -c "import vosk" >nul 2>&1',
        "if errorlevel 1 goto asr_fail",
        "echo  vosk 库安装成功",
        "echo.",
        "echo  第 3 步: 下载中文识别模型 [约 42MB]",
        'python "%~dp0_download_vosk.py"',
        "if errorlevel 1 goto asr_model_fail",
        "echo.",
        "echo  第 4 步: 首次运行会自动加载模型,约需 5-10 秒,属正常现象",
        "echo.",
        "echo  ==============================================",
        "echo   语音识别组件安装完成",
        "echo  ==============================================",
        "echo  使用方法:",
        "echo    1. 双击根目录 [一键运行.bat] 启动云智",
        "echo    2. 进入 [智能问答] 页面",
        "echo    3. 点输入框右侧的 [麦克风] 按钮开始说话",
        "echo    4. 说完再点一次 [结束],识别结果自动填入输入框",
        "echo.",
        "echo  已知限制:",
        "echo    纯普通话识别准确率高;英文缩写如 VPC / Docker 可能识别为音译汉字,",
        "echo    建议在输入框里手动补正后再发送。",
        "goto asr_end",
        "",
        ":asr_no_py",
        "echo  错误: 未检测到 Python,请先运行 tools\\安装Python.bat",
        "goto asr_end",
        "",
        ":asr_fail",
        "echo  错误: vosk 库安装失败,请检查网络后重试",
        "echo  手动命令: python -m pip install vosk -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "goto asr_end",
        "",
        ":asr_model_fail",
        "echo  错误: 模型下载失败",
        "echo  可稍后重跑本脚本;已下载部分会自动跳过",
        "echo  手动下载: https://alphacephei.com/vosk/models",
        "echo  下载 vosk-model-small-cn-0.22.zip 后解压到 models\\vosk 目录",
        "",
        ":asr_end",
        # 被 一键运行.bat 以 /silent 调用时不暂停，直接返回
        'if "%~1"=="/silent" exit /b 0',
    ] + footer_pause()

    write_bat("安装语音识别.bat", lines)


# ============================================================
# 2.57 tools/启动.bat —— 仅启动后端（不重复装大依赖）
# ============================================================
def build_start_only():
    title = "云智实训助手 - 后端启动程序"
    lines = header(title, up=True)
    lines += [
        "echo  [本脚本位于 tools 目录] 普通用户日常只需双击根目录 一键运行.bat",
        "echo.",
        "",
        "echo  第 1 步: 检查 Python 环境",
        "python --version >nul 2>&1",
        "if errorlevel 1 goto so_no_python",
        "python --version",
        "",
        "echo  第 2 步: 检查基础依赖 (flask / Pillow / bs4 / matplotlib)",
        'python -c "import flask" >nul 2>&1',
        "if errorlevel 1 goto so_install_deps",
        'python -c "import PIL" >nul 2>&1',
        "if errorlevel 1 goto so_install_deps",
        'python -c "import bs4" >nul 2>&1',
        "if errorlevel 1 goto so_install_deps",
        'python -c "import matplotlib" >nul 2>&1',
        "if errorlevel 1 goto so_install_deps",
        "echo  依赖已就绪",
        "goto so_check_ollama",
        "",
        ":so_install_deps",
        "echo  正在安装基础依赖 (不含 PyTorch,约 40MB)...",
        "python -m pip install flask Pillow beautifulsoup4 matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "if errorlevel 1 python -m pip install flask Pillow beautifulsoup4 matplotlib",
        'python -c "import flask" >nul 2>&1',
        "if errorlevel 1 goto so_install_fail",
        "echo  依赖安装成功",
        "",
        ":so_check_ollama",
        "echo.",
        "echo  第 3 步: 检查本地大模型 Ollama (可选)",
        "echo  说明: Ollama 为可选项,未安装也不影响知识库问答",
        "curl -s --max-time 2 http://localhost:11434/api/tags >nul 2>&1",
        "if errorlevel 1 goto so_no_ollama",
        "echo  Ollama 已在线,智能问答将启用本地大模型增强",
        "goto so_start_server",
        "",
        ":so_no_ollama",
        "echo  未检测到 Ollama,将使用 知识库+联网兜底 模式",
        "echo  如需启用大模型,请先安装 Ollama 并运行 ollama serve",
        "",
        ":so_start_server",
        "echo.",
        "echo  第 4 步: 启动后端服务",
        "echo  请稍候,浏览器会自动打开页面",
        "echo  地址: http://localhost:5000",
        "echo  关闭本窗口即可停止服务",
        "echo.",
        "python app.py",
        "echo.",
        "echo  服务已停止。",
        "goto so_end",
        "",
        ":so_no_python",
        "echo  错误: 未检测到 Python",
        "echo  请先运行 tools\\安装Python.bat,或访问 https://www.python.org/downloads/ 手动安装",
        "echo  安装时务必勾选 Add Python to PATH",
        "goto so_end",
        "",
        ":so_install_fail",
        "echo  错误: 依赖安装失败,请检查网络后重试",
        "echo  或手动运行: python -m pip install flask Pillow beautifulsoup4 matplotlib",
        "",
        ":so_end",
    ] + footer_pause()

    write_bat("启动.bat", lines)


def write_sd_downloader():
    """tools/_download_sd.py —— 并发 + 国内源优先 + 断点续传"""
    py_path = os.path.join(BASE_DIR, "_download_sd.py")
    content = '''# -*- coding: utf-8 -*-
"""
云智 SD 模型并发下载脚本
策略：国内源 (hf-mirror.com) 优先 -> 原版源 (huggingface.co) 回退
      多线程并发 + 断点续传 + 单文件重试
"""

import os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from huggingface_hub import hf_hub_download

REPO = "runwayml/stable-diffusion-v1-5"
MIRROR = "https://hf-mirror.com"

# (子目录/文件名, 远端路径, 是否必须, 描述)
FILES = [
    ("model_index.json",                    "model_index.json",                True,  "模型索引"),
    ("tokenizer/tokenizer_config.json",     "tokenizer/tokenizer_config.json", True,  "tokenizer 配置"),
    ("tokenizer/vocab.json",                "tokenizer/vocab.json",            True,  "词汇表"),
    ("tokenizer/merges.txt",                "tokenizer/merges.txt",            True,  "BPE 合并规则"),
    ("text_encoder/config.json",            "text_encoder/config.json",        True,  "text encoder 配置"),
    ("text_encoder/pytorch_model.bin",      "text_encoder/pytorch_model.bin",  True,  "text encoder 权重 (490MB)"),
    ("unet/config.json",                    "unet/config.json",                True,  "unet 配置"),
    ("unet/diffusion_pytorch_model.bin",    "unet/diffusion_pytorch_model.bin",True,  "unet 权重 (860MB, 最大)"),
    ("vae/config.json",                     "vae/config.json",                 True,  "vae 配置"),
    ("vae/diffusion_pytorch_model.bin",     "vae/diffusion_pytorch_model.bin", True,  "vae 权重 (334MB)"),
    ("scheduler/scheduler_config.json",     "scheduler/scheduler_config.json", True,  "scheduler 配置"),
]


def download_one(local_path, remote_path, desc):
    """单文件下载：国内源 -> 原版源，带重试"""
    if os.path.exists(local_path) and os.path.getsize(local_path) > 100:
        print(f"  [跳过] {desc} (已存在)")
        return True
    last_err = None
    for attempt in range(3):
        for mirror in [MIRROR, None]:  # 国内源优先，原版回退
            label = "国内源" if mirror else "原版源"
            try:
                if mirror:
                    os.environ["HF_ENDPOINT"] = mirror
                else:
                    os.environ.pop("HF_ENDPOINT", None)
                print(f"  [{label}] {desc} ...", flush=True)
                hf_hub_download(
                    repo_id=REPO,
                    filename=remote_path,
                    local_dir=os.path.dirname(local_path),
                    resume_download=True,  # 断点续传
                )
                print(f"  [OK] {desc}", flush=True)
                return True
            except Exception as e:
                last_err = e
                print(f"  [{label}] {desc} 失败: {type(e).__name__}", flush=True)
        print(f"  [重试 {attempt+1}/3] {desc}", flush=True)
    print(f"  [FAIL] {desc} 3 次均失败: {last_err}", flush=True)
    return False


def main():
    print("=" * 50)
    print("  云智 SD 模型并发下载")
    print("  策略:hf-mirror.com 优先 -> huggingface.co 回退")
    print("  4 线程并发 + 断点续传 + 单文件重试")
    print("=" * 50)

    # 工作目录 = bat 所在目录
    work_dir = os.path.dirname(os.path.abspath(__file__))
    target_root = os.path.join(work_dir, "models", "sd", REPO.replace("/", "_"))
    os.makedirs(target_root, exist_ok=True)

    print(f"目标目录: {target_root}")
    print(f"共 {len(FILES)} 个文件，并发 4 线程下载\\n")

    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {}
        for local_name, remote_path, required, desc in FILES:
            local_path = os.path.join(target_root, local_name)
            fut = ex.submit(download_one, local_path, remote_path, desc)
            futures[fut] = (required, desc, local_name)

        ok = 0
        for fut in as_completed(futures):
            required, desc, local_name = futures[fut]
            if fut.result():
                ok += 1
            elif required:
                pass  # 失败在 download_one 已打印

    print()
    if ok == len(FILES):
        print(f"[成功] 全部 {len(FILES)} 个文件下载完成")
        print(f"模型路径: {target_root}")
        print("接下来: 双击根目录 一键运行.bat -> 启动后进入「画图」页选「插画」类型")
        return 0
    else:
        print(f"[部分失败] {ok}/{len(FILES)} 个文件成功")
        print("如某文件失败可重跑本脚本，会自动断点续传")
        return 1


if __name__ == "__main__":
    sys.exit(main())
'''
    with open(py_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已生成: tools/_download_sd.py  ({len(content)} 字节)")


# ============================================================
# 2.6 根目录/一键运行.bat —— 唯一入口
#     环境检测(含安装位置) + 缺啥补啥 + 可选组件详细说明 + 启动
# ============================================================
def build_one_click_run():
    title = "云智实训助手 - 一键运行"
    lines = header(title)
    lines += [
        'if "%~1"=="/auto" set "OC_AUTO=1"',
        'if "%~1"=="/AUTO" set "OC_AUTO=1"',
        'if "%OC_AUTO%"=="1" echo  [全自动模式] 必选组件缺失自动安装,可选项默认装 qwen2.5:3b',
        'if "%OC_AUTO%"=="1" echo.',
        "",
        "echo ----------------------------------------------",
        f"echo  {c('第 1 步 [必选] 检测 Python 环境', 'info')}",
        "echo ----------------------------------------------",
        "python --version >nul 2>&1",
        "if errorlevel 1 goto oc_py_need",
        "python --version",
        "where python",
        f"echo  状态: {c('已安装','ok')}",
        "goto oc_chk_dep",
        "",
        ":oc_py_need",
        "echo  状态: 未安装 [必选组件,自动开始安装]",
        "echo  安装方式: winget 优先,失败回退华为云镜像/官网",
        "where winget >nul 2>&1",
        "if errorlevel 1 goto oc_py_curl",
        "winget install Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements",
        "if not errorlevel 1 goto oc_py_refresh",
        "echo  winget 失败,改用安装包方式...",
        "",
        ":oc_py_curl",
        'set "PYEXE=%TEMP%\\yunzhi_py\\python-3.11.9-amd64.exe"',
        'if not exist "%TEMP%\\yunzhi_py" mkdir "%TEMP%\\yunzhi_py"',
        "curl -L -o \"%PYEXE%\" \"https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-amd64.exe\" --connect-timeout 30",
        'if exist "%PYEXE%" goto oc_py_install',
        "curl -L -o \"%PYEXE%\" \"https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe\" --connect-timeout 30",
        'if exist "%PYEXE%" goto oc_py_install',
        "goto oc_py_fail",
        "",
        ":oc_py_install",
        "echo  正在静默安装,约需 1 分钟,请勿关闭窗口...",
        'if exist "%PYEXE%" "%PYEXE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0',
        "",
        ":oc_py_refresh",
        'set "PATH=%PATH%;%LOCALAPPDATA%\\Programs\\Python\\Python311;%LOCALAPPDATA%\\Programs\\Python\\Python311\\Scripts"',
        "python --version >nul 2>&1",
        "if errorlevel 1 goto oc_py_warn",
        "python --version",
        "echo  状态: 安装成功",
        "goto oc_chk_dep",
        "",
        ":oc_py_warn",
        "echo  Python 已安装但当前窗口未识别,请关闭窗口后重新双击本文件",
        "goto oc_end",
        "",
        ":oc_py_fail",
        "echo  错误: 自动安装失败,请手动安装 Python 3.11",
        "echo  下载: https://www.python.org/downloads/  务必勾选 Add Python to PATH",
        "goto oc_end",
        "",
        # ---------- 依赖 ----------
        ":oc_chk_dep",
        "echo.",
        "echo ----------------------------------------------",
        f"echo  {c('第 2 步 [必选] 检测后端依赖', 'info')}",
        "echo ----------------------------------------------",
        'python -c "import flask" >nul 2>&1',
        "if errorlevel 1 goto oc_dep_install",
        'python -c "import bs4" >nul 2>&1',
        "if errorlevel 1 goto oc_dep_install",
        'python -c "import PIL" >nul 2>&1',
        "if errorlevel 1 goto oc_dep_install",
        'python -c "import matplotlib" >nul 2>&1',
        "if errorlevel 1 goto oc_dep_install",
        f"echo  状态: {c('已就绪', 'ok')} [flask / Pillow / beautifulsoup4 / matplotlib]",
        "",
        # 可选依赖：OCR（pytesseract）—— 缺失不影响核心功能，仅 /api/ocr 不可用
        "echo.",
        f"echo  {c('可选依赖检测', 'info')}: OCR 截图识别 (pytesseract)",
        'python -c "import pytesseract" >nul 2>&1',
        "if errorlevel 1 goto oc_ocr_missing",
        f"echo   {c('已安装', 'ok')} pytesseract (OCR 可用)",
        "goto oc_chk_ollama",
        "",
        ":oc_ocr_missing",
        f"echo   {c('未安装', 'warn')} pytesseract [OCR 截图识别不可用,排错诊断仍支持手动输入]",
        "echo   一键补装: 运行 tools\\安装OCR依赖.bat",
        "echo   或命令: python -m pip install pytesseract",
        "echo           此外需安装 Tesseract 程序: https://github.com/tesseract-ocr/tesseract",
        "goto oc_chk_ollama",
        "",
        ":oc_dep_install",
        f"echo  状态: {c('缺失,自动安装中', 'warn')} [约 5MB,首次约 1-3 分钟,清华镜像源]...",
        "python -m pip install flask Pillow beautifulsoup4 matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "if errorlevel 1 python -m pip install flask Pillow beautifulsoup4 matplotlib",
        'python -c "import flask" >nul 2>&1',
        "if errorlevel 1 goto oc_dep_fail",
        'python -c "import matplotlib" >nul 2>&1',
        "if errorlevel 1 goto oc_dep_fail",
        f"echo  状态: {c('安装成功', 'ok')}",
        "goto oc_chk_ollama",
        "",
        ":oc_dep_fail",
        f"echo  {c('错误: 依赖安装失败', 'err')},请检查网络后重新双击本文件",
        "goto oc_end",
        "",
    ]

    # ---------- Ollama 检测 ----------
    lines += [
        ":oc_chk_ollama",
        "echo.",
        "echo ----------------------------------------------",
        f"echo  {c('第 3 步 [可选] 检测 Ollama 大模型服务', 'info')}",
        "echo ----------------------------------------------",
        "where ollama >nul 2>&1",
        "if errorlevel 1 goto oc_ol_missing",
        f"echo  状态: {c('已安装', 'ok')}",
        "where ollama",
        # 版本号 + 服务状态：先落文件过滤掉 Windows 下的 stderr 噪声行
        'ollama --version > "%TEMP%\\yz_ver.txt" 2>&1',
        'findstr /V /C:"failed to get console mode" "%TEMP%\\yz_ver.txt" 2>nul',
        "curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1",
        "if errorlevel 1 goto oc_ol_off",
        f"echo          服务状态 : {c('在线', 'ok')} [http://localhost:11434]",
        "set \"OC_OLLOK=1\"",
        "goto oc_chk_models",
        "",
        ":oc_ol_off",
        f"echo          服务状态 : {c('未运行', 'warn')} - 请打开开始菜单搜索 Ollama 点击运行",
        "goto oc_chk_models",
        "",
        ":oc_ol_missing",
        f"echo  状态: {c('未安装', 'warn')}",
        "echo  --------------------------------------------------------------",
        "echo   Ollama 是什么 : 在你电脑上本地运行大模型的引擎,推理全程离线",
        "echo   装了之后      : 云智把联网搜索结果交给大模型,总结成完整回答",
        "echo   不装会怎样    : 不影响使用! 知识库问答/联网搜索/任务引导/",
        "echo                   排错诊断/报告生成 全部正常,",
        "echo                   仅联网兜底从 [模型总结] 降级为 [罗列搜索结果]",
        "echo   以后想装      : 运行 tools\\一键安装.bat 或 tools\\安装Ollama.bat",
        "echo   装完怎么跑    : 开机自动启动;手动启动: 开始菜单搜索 Ollama",
        "echo  ----------------------------------------------------------------",
        'if exist "%~dp0.yz_skip_ollama" echo   提示: 你之前选择跳过,删除根目录 .yz_skip_ollama 可重新询问',
        'if exist "%~dp0.yz_skip_ollama" goto oc_chk_models',
        'if "%OC_AUTO%"=="1" goto oc_ol_do_install',
        "",
        'set "ANS="',
        'set /p "ANS=  是否现在安装 Ollama? [1=安装 / 2=跳过并记住,回车默认跳过]: "',
        'if "%ANS%"=="1" goto oc_ol_do_install',
        "",
        ":oc_ol_skip_now",
        "echo skipped>" + '"%~dp0.yz_skip_ollama"',
        'if exist "%~dp0.yz_skip_ollama" attrib +h "%~dp0.yz_skip_ollama" >nul 2>&1',
        "echo  已跳过并记住,以后可运行 tools\\一键安装.bat 补装",
        "goto oc_chk_models",
        "",
":oc_ol_do_install",
        "echo  正在下载 Ollama [来源 ollama.com 原版],约 200MB...",
        "if exist ollama-installer.exe goto oc_ol_run",
        "curl -L --retry 3 --retry-delay 5 -C - -o ollama-installer.exe --connect-timeout 15 --max-time 3600 https://ollama.com/download/OllamaSetup.exe",
        "if not errorlevel 1 goto oc_ol_run",
        "echo  curl 失败,尝试 PowerShell...",
        "del ollama-installer.exe >nul 2>&1",
        "powershell -NoProfile -ExecutionPolicy Bypass -Command try { Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'ollama-installer.exe' -UseBasicParsing } catch { exit 1 }",
        "if not errorlevel 1 goto oc_ol_run",
        "del ollama-installer.exe >nul 2>&1",
        "echo.",
        "echo  错误: Ollama 下载失败",
        "echo  请手动访问 https://ollama.com/download 下载 OllamaSetup.exe",
        "echo  把下载的文件放到本目录并重命名为 ollama-installer.exe",
        "echo  然后重新双击本文件即可自动安装",
        "goto oc_chk_models",
        "",
        ":oc_ol_run",
        'if not exist ollama-installer.exe goto oc_chk_models',
        "echo  正在静默安装,可能弹出 UAC 确认...",
        "ollama-installer.exe /S",
        "del ollama-installer.exe >nul 2>&1",
        "echo  等待服务就绪,约 10-15 秒...",
        "ping -n 12 127.0.0.1 >nul",
        "curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1",
        "if errorlevel 1 goto oc_chk_models",
        'set "OC_OLLOK=1"',
        "echo  Ollama 安装成功",
        "",
    ]

    # ---------- 大模型检测 ----------
    lines += [
        ":oc_chk_models",
        "echo.",
        f"echo {c('----------------------------------------------', 'info')}",
        f"echo  {c('第 4 步 [可选] 检测大模型', 'info')}",
        "echo ----------------------------------------------",
        'if not "%OC_OLLOK%"=="1" goto oc_md_no_ollama',
        "",
        # 先把 ollama list 结果落到临时文件（同时吞掉 stderr 的英文报错），
        # 再用 findstr 过滤表头和 "failed to get console mode" 噪声行
        'ollama list > "%TEMP%\\yz_ml_raw.txt" 2>&1',
        'findstr /V /C:"NAME" /C:"failed to get console mode" "%TEMP%\\yz_ml_raw.txt" > "%TEMP%\\yz_ml.txt" 2>nul',
        # 判断是否真的有模型：ollama 模型名一定含冒号（如 qwen2.5:3b）
        # 这样即使有其它噪声行也不会误判
        'findstr /C:":" "%TEMP%\\yz_ml.txt" >nul 2>&1',
        'if errorlevel 1 goto oc_md_missing',
        f"echo  {c('当前已装模型：', 'val')}",
        'type "%TEMP%\\yz_ml.txt"',
        "echo.",
        f"echo  {c('状态: 已有可用模型，无需重复下载', 'ok')}",
        f"echo          模型目录 : {c('%USERPROFILE%', 'info')}\\.ollama\\models",
        'set "OC_MODEL_OK=1"',
        # 已装模型时也给出「想再加一个」的入口
        'set "MDMORE="',
        'set /p "MDMORE=  是否还要再装一个模型? [1=继续选择 / 回车=跳过]: "',
        'if "%MDMORE%"=="1" goto oc_md_menu',
        "goto oc_chk_sd",
        "",
        ":oc_md_missing",
        f"echo  {c('当前已装模型：', 'val')}(无)",
        f"echo  {c('状态: 未下载任何模型', 'warn')}",
        "echo    大模型是什么 : 会回答的脑子,下载后存放在:",
        f"echo                  {c('%USERPROFILE%', 'info')}\\.ollama\\models",
        "echo    不装会怎样   : 不影响核心功能,联网兜底直接罗列搜索结果",
        "echo    以后想装     : 运行 tools\\一键安装.bat 或 tools\\安装模型_xxx.bat",
        "echo    释放磁盘     : 命令行执行 ollama rm 模型名 即可删除",
        'if exist "%~dp0.yz_skip_model" echo    提示: 你之前选择跳过,删除根目录 .yz_skip_model 可重新询问',
        'if exist "%~dp0.yz_skip_model" goto oc_chk_sd',
        'if "%OC_AUTO%"=="1" set "MDSEL=1" & goto oc_md_pull',
        "goto oc_md_menu",
        "",
        ":oc_md_menu",
        f"echo  {c('请选择要添加/下载的模型', 'val')} [绿色=本机已装,黄色=需下载;只影响回答质量,不影响功能]:",
    ]
    # 菜单：逐项判断是否已装，加 [已安装]/[需下载] 标记
    # 统一读 yz_ml_raw.txt（在 :oc_chk_models 已生成），避免 ollama list 的 stdout 噪声
    for i, m in enumerate(MODELS, 1):
        tag = m["tag"]
        lines.append(
            f'<nul set /p "=  [{i}] {tag.ljust(19)} {m["size"].ljust(9)} {m["use"]}  "'
        )
        lines.append(
            f'findstr /I /C:"{tag}" "%TEMP%\\yz_ml_raw.txt" >nul 2>&1 '
            f'&& (echo {c("[已安装]", "ok")}) || (echo {c("[需下载]", "warn")})'
        )
    lines += [
        "echo   [0] 跳过 [回车默认]",
        'set "MDSEL="',
        'set /p "MDSEL=  请选择 [0-6]: "',
    ]
    for i, m in enumerate(MODELS, 1):
        lines.append(f'if "%MDSEL%"=="{i}" set "MDSEL_TAG={m["tag"]}" & goto oc_md_pull')
    lines += [
        "goto oc_md_skip_now",
        "",
        ":oc_md_pull",
        'if "%OC_AUTO%"=="1" set "MDSEL_TAG=qwen2.5:3b"',
        f"echo  正在拉取 {c('%MDSEL_TAG%','val')} [首次需几分钟,请勿关闭窗口]...",
        'ollama list > "%TEMP%\\yz_ml2.txt" 2>&1',
        'findstr /I /C:"%MDSEL_TAG%" "%TEMP%\\yz_ml2.txt" >nul 2>&1',
        "if not errorlevel 1 goto oc_md_already",
        "ollama pull %MDSEL_TAG%",
        "if errorlevel 1 goto oc_md_pull_fail",
        'set "OC_MODEL_OK=1"',
        f"echo  {c('模型下载完成', 'ok')}",
        "goto oc_md_after_pull",
        "",
        # 用户选了菜单里「已安装」的模型 → 直接跳过，不重复下载
        ":oc_md_already",
        f"echo  {c('该模型本机已安装，跳过下载', 'ok')}",
        'set "OC_MODEL_OK=1"',
        "goto oc_md_after_pull",
        "",
        ":oc_md_after_pull",
        "echo.",
        'ollama list > "%TEMP%\\yz_ml3.txt" 2>&1',
        'findstr /V /B /C:"NAME" /C:"failed" "%TEMP%\\yz_ml3.txt" > "%TEMP%\\yz_ml.txt" 2>nul',
        f"echo  {c('当前已装模型：', 'val')}",
        'type "%TEMP%\\yz_ml.txt"',
        "goto oc_chk_sd",
        "",
        ":oc_md_pull_fail",
        f"echo  {c('警告: 下载失败', 'err')} [网络/磁盘/Ollama 异常],可稍后运行 tools\\一键安装.bat 重试",
        "goto oc_chk_sd",
        "",
        ":oc_md_skip_now",
        "echo skipped>" + '"%~dp0.yz_skip_model"',
        'if exist "%~dp0.yz_skip_model" attrib +h "%~dp0.yz_skip_model" >nul 2>&1',
        "echo  已跳过并记住,以后可运行 tools\\一键安装.bat 补装",
        "goto oc_chk_sd",
        "",
        ":oc_md_no_ollama",
        f"echo  {c('状态: 未启用', 'warn')} [需要先安装并启动 Ollama]",
        "echo    不装会怎样   : 不影响核心功能,联网兜底直接罗列搜索结果",
        "",

        # ---------- SD 检测（可选 3/3）----------
        ":oc_chk_sd",
        "echo.",
        "echo ----------------------------------------------",
        f"echo  {c('第 5 步 [可选] 检测 Stable Diffusion 画图模型', 'info')}",
        "echo ----------------------------------------------",
        # 缺任何 SD 依赖（modelscope/torch/diffusers/transformers/accelerate/safetensors/huggingface_hub）：
        # 跳到 oc_sd_nodep 处理（自动模式会自动装）
        'python -c "import modelscope, torch, diffusers, transformers, accelerate, safetensors, huggingface_hub" >nul 2>&1',
        'if errorlevel 1 goto oc_sd_nodep',
        # 模型是否真正就绪：必须 4 个关键文件都在（model_index.json + 3 个权重 .bin）
        'if not exist "%CD%\\models\\sd\\runwayml_stable-diffusion-v1-5\\model_index.json" goto oc_sd_need_dl',
        'if not exist "%CD%\\models\\sd\\runwayml_stable-diffusion-v1-5\\unet\\diffusion_pytorch_model.bin" goto oc_sd_need_dl',
        'if not exist "%CD%\\models\\sd\\runwayml_stable-diffusion-v1-5\\vae\\diffusion_pytorch_model.bin" goto oc_sd_need_dl',
        'if not exist "%CD%\\models\\sd\\runwayml_stable-diffusion-v1-5\\text_encoder\\pytorch_model.bin" goto oc_sd_need_dl',
        'goto oc_sd_have',
        "",
        f"echo  状态: {c('未下载', 'warn')} [依赖已就绪,可随时下载]",
        "echo  ----------------------------------------------------------------",
        "echo   SD 是什么 : 本地运行 Stable Diffusion 出插画的模型",
        "echo   不装会怎样: 不影响核心功能! 拓扑图仍可用 (matplotlib)",
        "echo                仅插画类 prompt 走 SD 出图;不装则降级为拓扑图",
        "echo   存放位置  : %CD%\\models\\sd\\runwayml_stable-diffusion-v1-5",
        "echo   大小      : 约 4.2 GB (国内源优先下载)",
        "echo   以后想装  : 运行 tools\\下载StableDiffusion.bat",
        "echo  ----------------------------------------------------------------",
        'if exist "%~dp0.yz_skip_sd" echo   提示: 你之前选择跳过,删除根目录 .yz_skip_sd 可重新询问',
        'if exist "%~dp0.yz_skip_sd" goto oc_chk_asr',
        'if "%OC_AUTO%"=="1" goto oc_sd_install',
        "",
        'set "SD_ANS="',
        'set /p "SD_ANS=  是否现在下载 SD 模型? [1=下载 / 2=跳过并记住,回车默认跳过]: "',
        'if "%SD_ANS%"=="1" goto oc_sd_install',
        "goto oc_sd_skip",
        "",

        # --- 缺 torch/diffusers：手动模式提示，自动模式自动装 ---
        ":oc_sd_nodep",
        f"echo  {c('状态: 插画功能依赖缺失', 'warn')} [缺少 PyTorch / diffusers]",
        "echo  ----------------------------------------------------------------",
        'if "%OC_AUTO%"=="1" goto oc_sd_dep_install_auto',
        "echo   原因    : 出插画需要 PyTorch + diffusers,当前检测到未安装",
        "echo   影响    : 仅「插画」出图不可用;拓扑/架构图 (matplotlib) 不受影响",
        "echo   一键补装: 运行 tools\\安装画图依赖.bat (约 2-3GB,国内源)  <== 推荐",
        "echo   或命令  : python -m pip install torch diffusers transformers accelerate",
        "echo             safetensors -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "echo  ----------------------------------------------------------------",
        "goto oc_chk_asr",
        "",
        ":oc_sd_dep_install_auto",
        f"echo  {c('[自动模式] 正在安装 PyTorch + diffusers (约 2-3GB,首次需 5-15 分钟)', 'warn')}...",
        "echo.",
        'call "%~dp0tools\\安装画图依赖.bat"',
        "echo.",
        # 装完重新检测：还缺就降级（不阻塞启动）
        'python -c "import modelscope, torch, diffusers, transformers, accelerate, safetensors, huggingface_hub" >nul 2>&1',
        "if errorlevel 1 goto oc_sd_nodep_after_install",
        # 依赖 OK 但模型还没下 → 继续走下载
        f"echo  {c('依赖装好了，现在开始下载 SD 模型...', 'ok')}",
        "goto oc_sd_install",
        "",
        ":oc_sd_nodep_after_install",
        f"echo  {c('[自动模式] 依赖安装失败', 'err')},跳过 SD,降级为「拓扑图」模式",
        "echo  ----------------------------------------------------------------",
        "echo   影响    : 仅「插画」出图不可用;拓扑/架构图 (matplotlib) 不受影响",
        "echo   以后想装: 运行 tools\\安装画图依赖.bat 重试",
        "echo  ----------------------------------------------------------------",
        "goto oc_chk_asr",
        "",
        # --- 依赖 OK 但模型未下 / 下不全：提示下载 ---
        ":oc_sd_need_dl",
        f"echo  状态: {c('未下载', 'warn')} [依赖已就绪,可随时下载]",
        "echo  ----------------------------------------------------------------",
        "echo   SD 是什么 : 本地运行 Stable Diffusion 出插画的模型",
        "echo   不装会怎样: 不影响核心功能! 拓扑图仍可用 (matplotlib)",
        "echo                仅插画类 prompt 走 SD 出图;不装则降级为拓扑图",
        "echo   存放位置  : %CD%\\models\\sd\\runwayml_stable-diffusion-v1-5",
        "echo   大小      : 约 4.2 GB (国内源优先下载)",
        "echo   以后想装  : 运行 tools\\下载StableDiffusion.bat",
        "echo  ----------------------------------------------------------------",
        'if exist "%~dp0.yz_skip_sd" echo   提示: 你之前选择跳过,删除根目录 .yz_skip_sd 可重新询问',
        'if exist "%~dp0.yz_skip_sd" goto oc_chk_asr',
        'if "%OC_AUTO%"=="1" goto oc_sd_install',
        "",
        'set "SD_ANS="',
        'set /p "SD_ANS=  是否现在下载 SD 模型? [1=下载 / 2=跳过并记住,回车默认跳过]: "',
        'if "%SD_ANS%"=="1" goto oc_sd_install',
        "goto oc_sd_skip",
        "",
        ":oc_sd_install",
        "echo  正在调用 tools\\下载StableDiffusion.bat ...",
        'call "%~dp0tools\\下载StableDiffusion.bat"',
        "goto oc_sd_done",
        "",
        ":oc_sd_skip",
        "echo skipped>" + '"%~dp0.yz_skip_sd"',
        'if exist "%~dp0.yz_skip_sd" attrib +h "%~dp0.yz_skip_sd" >nul 2>&1',
        "echo  已跳过并记住,以后可运行 tools\\下载StableDiffusion.bat 补装",
        "goto oc_chk_asr",
        "",
        ":oc_sd_have",
        f"echo  状态: {c('已下载', 'ok')} [依赖已就绪]",
        'set "OC_SD_OK=1"',
        "echo          模型目录 : %CD%\\models\\sd\\runwayml_stable-diffusion-v1-5",
        "",
        ":oc_sd_done",
    ]

    # ---------- 语音识别检测（可选 4/4）----------
    lines += [
        ":oc_chk_asr",
        "echo.",
        "echo ----------------------------------------------",
        f"echo  {c('第 6 步 [可选] 检测语音识别组件', 'info')}",
        "echo ----------------------------------------------",
        'python -c "import vosk" >nul 2>&1',
        "if errorlevel 1 goto oc_asr_missing",
        'if not exist "%~dp0models\\vosk\\am\\final.mdl" goto oc_asr_missing',
        f"echo  状态: {c('已就绪', 'ok')} [麦克风语音输入可用,本地离线识别,音频不外发]",
        'set "OC_ASR_OK=1"',
        "goto oc_summary",
        "",
        ":oc_asr_missing",
        f"echo  状态: {c('未启用', 'warn')} [语音输入不可用,键盘输入完全不受影响]",
        "echo  ----------------------------------------------------------------",
        "echo   语音输入是什么: 智能问答页点麦克风,用普通话直接说话提问",
        "echo   装了之后      : 学生不用打字,说完自动转成文字填进输入框",
        "echo   不装会怎样    : 不影响任何功能,学生仍可键盘输入问题",
        "echo   大小          : 约 45MB [库 3MB + 中文模型 42MB],约 1-3 分钟",
        "echo   数据说明      : 纯本地离线识别,音频不上传任何外部服务器",
        "echo   以后想装      : 运行 tools\\安装语音识别.bat",
        "echo  ----------------------------------------------------------------",
        'if exist "%~dp0.yz_skip_asr" echo   提示: 你之前选择跳过,删除根目录 .yz_skip_asr 可重新询问',
        'if exist "%~dp0.yz_skip_asr" goto oc_summary',
        'if "%OC_AUTO%"=="1" goto oc_asr_install',
        "",
        'set "ASR_ANS="',
        'set /p "ASR_ANS=  是否安装语音识别组件? [1=安装(推荐) / 2=跳过并记住,回车默认安装]: "',
        'if "%ASR_ANS%"=="2" goto oc_asr_skip',
        "goto oc_asr_install",
        "",
        ":oc_asr_install",
        "echo.",
        f"echo  {c('正在安装语音识别组件 [约 45MB],请稍候 1-3 分钟...', 'info')}",
        # 子脚本会 cd 到项目根，call 前后保存/恢复当前目录
        'set "OC_PWD=%CD%"',
        'call "%~dp0tools\\安装语音识别.bat" /silent',
        'cd /d "%OC_PWD%"',
        'python -c "import vosk" >nul 2>&1',
        "if errorlevel 1 goto oc_asr_fail",
        'if not exist "%~dp0models\\vosk\\am\\final.mdl" goto oc_asr_fail',
        'set "OC_ASR_OK=1"',
        f"echo  {c('语音识别组件安装完成,麦克风语音输入已可用', 'ok')}",
        "goto oc_summary",
        "",
        ":oc_asr_fail",
        f"echo  {c('语音识别组件安装失败', 'err')} [不影响其他功能]",
        "echo    可稍后运行 tools\\安装语音识别.bat 重试,或直接用键盘输入问题",
        "goto oc_summary",
        "",
        ":oc_asr_skip",
        "echo skipped>" + '"%~dp0.yz_skip_asr"',
        'if exist "%~dp0.yz_skip_asr" attrib +h "%~dp0.yz_skip_asr" >nul 2>&1',
        "echo  已跳过并记住,以后可运行 tools\\安装语音识别.bat 补装",
        "goto oc_summary",
        "",
    ]

    # ---------- 汇总 + 启动 ----------
    # 汇总用变量保存彩色"可用/未启用"文本，便于 if 分支复用
    OKTXT = c("可用", "ok")
    NOTXT = c("未启用", "warn")
    lines += [
        ":oc_summary",
        'set "OKTXT=' + OKTXT + '"',
        'set "NOTXT=' + NOTXT + '"',
        "echo.",
        "echo ----------------------------------------------",
        f"echo  {c('检测完成 - 当前可用功能', 'info')}",
        "echo ----------------------------------------------",
        f"echo   知识库问答 / 任务引导 / 排错诊断 / 报告生成 : {c('可用','ok')}",
        f"echo   联网搜索兜底                               : {c('可用','ok')}",
        f"echo   拓扑/架构图 (matplotlib)                   : {c('可用','ok')}",
        'if "%OC_SD_OK%"=="1" echo   插画出图 (Stable Diffusion)               : %OKTXT%',
        'if not "%OC_SD_OK%"=="1" echo   插画出图 (Stable Diffusion)               : %NOTXT%',
        'if "%OC_MODEL_OK%"=="1" echo   大模型总结回答                             : %OKTXT%',
        'if not "%OC_MODEL_OK%"=="1" echo   大模型总结回答                             : %NOTXT%',
        'if "%OC_ASR_OK%"=="1" echo   语音输入 (Vosk 本地离线)                  : %OKTXT%',
        'if not "%OC_ASR_OK%"=="1" echo   语音输入 (Vosk 本地离线)                  : %NOTXT%',
        f"echo   {c('提示: 以上「未启用」项不影响其他功能,可随时补装', 'val')}",
        'if "%OC_AUTO%"=="1" goto oc_launch',
        "",
        'set "LA="',
        'set /p "LA=  按回车立即启动云智 [或输入 2 退出]: "',
        'if "%LA%"=="2" goto oc_quit',
        "",
        ":oc_launch",
        "echo.",
        # 启动前最后一道自检：扫描所有依赖并给出友好提示（不阻断启动）
        f"echo  {c('启动前自检', 'info')}: 扫描所有依赖...",
        'python check_deps.py',
        "echo.",
        f"echo  {c('正在启动', 'ok')},浏览器将自动打开 http://localhost:5000",
        "echo  关闭本窗口即停止服务",
        "echo.",
        "python app.py",
        "goto oc_end",
        "",
        ":oc_quit",
        "echo  已退出。以后使用只需双击本文件。",
        "",
        ":oc_end",
        "echo.",
        "pause",
        "exit /b",
    ]

    write_bat("一键运行.bat", lines, root=True)


# ============================================================
# 3. tools/一键安装.bat —— 交互式安装向导（必选自动 + 可选菜单）
# ============================================================
def build_unified_installer():
    """生成 一键安装.bat

    结构（对齐用户需求：必选 + 可选）：
        [必选] Python 环境        —— 自动检测，缺了才装，无需选择
        [必选] 后端依赖           —— 自动检测，缺了才装，无需选择
        [可选] Ollama 大模型服务  —— 询问 [1=安装 / 2=跳过]
        [可选] 大模型下载 6 选 1  —— 询问 [1-6]，0=跳过
        收尾   询问是否立即启动

    模式：
        双击运行        = 向导模式（可选步骤逐项询问）
        一键安装.bat /auto = 全自动模式（必选+Ollama+qwen2.5:3b 装齐后直接启动）

    设计约束：
        - 每一步都可重复运行（已装自动跳过），向导可断点续跑
        - Ollama/模型未装不影响必选步骤，装完依赖即可用
          知识库问答 + 联网兜底
        - 全部逻辑内嵌，不依赖其他 bat（删掉旧脚本也能独立工作）
    """
    title = "云智实训助手 - 环境一键安装向导"
    lines = header(title, up=True)

    # ---------- 横幅说明 ----------
    lines += [
        "echo  本向导一次性装齐运行环境",
        "echo  [本文件位于 tools 目录,日常使用只需双击根目录 一键运行.bat]",
        "echo.",
        "echo  [必选] Python 环境",
        "echo    作用      : 云智后端程序的运行基础",
        "echo    不装会怎样: 系统完全无法启动,属于必装 [自动检测缺了才装]",
        "echo    存放位置  : %LOCALAPPDATA%\\Programs\\Python\\Python311",
        "echo    怎么运行  : 安装时自动加入 PATH,之后任意窗口敲 python 即可",
        "echo.",
        "echo  [必选] 后端依赖",
        "echo    作用      : flask 网站框架 / beautifulsoup4 联网搜索解析 等",
        "echo    不装会怎样: 系统无法启动,属于必装 [自动检测缺了才装]",
        "echo.",
        "echo  [可选] Ollama 大模型服务",
        "echo    作用      : 在你电脑上本地运行大模型的引擎,推理全程离线",
        "echo    不装会怎样: 不影响使用! 知识库问答/联网搜索/任务引导/",
        "echo                排错诊断/报告生成 全部正常,",
        "echo                仅联网兜底从 [模型总结] 降级为 [罗列搜索结果]",
        "echo    存放位置  : %LOCALAPPDATA%\\Programs\\Ollama",
        "echo    怎么运行  : 开机自动启动;手动启动: 开始菜单搜索 Ollama",
        "echo.",
        "echo  [可选] 大模型下载 6 选 1",
        "echo    作用      : 会回答的脑子,按电脑内存选择,推荐 qwen2.5:3b",
        "echo    不装会怎样: 不影响核心功能,联网兜底直接罗列搜索结果",
        "echo    存放位置  : %USERPROFILE%\\.ollama\\models",
        "echo    释放磁盘  : 命令行执行 ollama rm 模型名 即可删除",
        "echo.",
        'if "%~1"=="/auto" set "AUTO_MODE=1"',
        'if "%~1"=="/AUTO" set "AUTO_MODE=1"',
        'if "%AUTO_MODE%"=="1" echo  *** 全自动模式: 必选组件 + Ollama + qwen2.5:3b 自动装齐 ***',
        'if "%AUTO_MODE%"=="1" echo.',
        "",
    ]

    # ---------- 必选 1/2: Python ----------
    lines += [
        "echo ----------------------------------------------",
        "echo  [必选 1/2] 检查 Python 环境",
        "echo ----------------------------------------------",
        "python --version >nul 2>&1",
        "if errorlevel 1 goto py_need",
        "python --version",
        "echo  Python 已就绪",
        "goto step_dep",
        "",
        ":py_need",
        "echo  未检测到 Python,开始自动安装...",
        "where winget >nul 2>&1",
        "if errorlevel 1 goto py_curl",
        "echo  正在通过 winget 安装 Python 3.11,请稍候...",
        "winget install Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements",
        "if not errorlevel 1 goto py_refresh",
        "echo  winget 安装失败,改用下载安装包方式",
        "echo.",
        "",
        ":py_curl",
        'set "PYEXE=%TEMP%\\yunzhi_py\\python-3.11.9-amd64.exe"',
        'if not exist "%TEMP%\\yunzhi_py" mkdir "%TEMP%\\yunzhi_py"',
        "echo  正在从华为云镜像下载 Python 3.11 安装包...",
        'curl -L -o "%PYEXE%" "https://mirrors.huaweicloud.com/python/3.11.9/python-3.11.9-amd64.exe" --connect-timeout 30',
        'if exist "%PYEXE%" goto py_install',
        "echo  华为云镜像失败,尝试 Python 官网...",
        'curl -L -o "%PYEXE%" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" --connect-timeout 30',
        'if exist "%PYEXE%" goto py_install',
        "goto py_fail",
        "",
        ":py_install",
        "echo  正在静默安装 Python,约需 1 分钟,请勿关闭窗口...",
        'if "%AUTO_MODE%"=="1" echo  [auto] 后台安装中,完成后自动继续',
        'set "PYEXE=%TEMP%\\yunzhi_py\\python-3.11.9-amd64.exe"',
        'if exist "%PYEXE%" "%PYEXE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0',
        "",
        ":py_refresh",
        "echo  正在刷新当前窗口的 PATH...",
        'set "PATH=%PATH%;%LOCALAPPDATA%\\Programs\\Python\\Python311;%LOCALAPPDATA%\\Programs\\Python\\Python311\\Scripts"',
        "python --version >nul 2>&1",
        "if errorlevel 1 goto py_path_warn",
        "python --version",
        "echo  Python 安装成功",
        "goto step_dep",
        "",
        ":py_path_warn",
        "echo  警告: Python 已安装,但当前窗口未能立即识别",
        "echo  请关闭本窗口,重新双击本向导,会自动从下一步继续",
        "goto end_pause",
        "",
        ":py_fail",
        "echo  错误: Python 自动安装失败",
        "echo  请手动安装 Python 3.11:",
        "echo    1. 打开 https://www.python.org/downloads/",
        "echo    2. 安装时务必勾选 Add Python to PATH",
        "echo    3. 完成后重新运行本向导",
        "goto end_pause",
        "",
    ]

    # ---------- 必选 2/2: 后端依赖 ----------
    lines += [
        ":step_dep",
        "echo.",
        "echo ----------------------------------------------",
        "echo  [必选 2/2] 检查后端依赖",
        "echo ----------------------------------------------",
        'python -c "import flask" >nul 2>&1',
        "if errorlevel 1 goto dep_install",
        'python -c "import bs4" >nul 2>&1',
        "if errorlevel 1 goto dep_install",
        'python -c "import PIL" >nul 2>&1',
        "if errorlevel 1 goto dep_install",
        'python -c "import matplotlib" >nul 2>&1',
        "if errorlevel 1 goto dep_install",
        "echo  依赖已就绪 [flask / Pillow / bs4 / matplotlib]",
        "goto step_ollama",
        "",
        ":dep_install",
        "echo  正在安装依赖 flask / Pillow / beautifulsoup4 / matplotlib ...",
        "echo  首次约需 1-3 分钟,优先使用清华镜像源...",
        "python -m pip install flask Pillow beautifulsoup4 matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple",
        "if errorlevel 1 python -m pip install flask Pillow beautifulsoup4 matplotlib",
        'python -c "import flask" >nul 2>&1',
        "if errorlevel 1 goto dep_fail",
        'python -c "import matplotlib" >nul 2>&1',
        "if errorlevel 1 goto dep_fail",
        "echo  依赖安装成功",
        "goto step_ollama",
        "",
        ":dep_fail",
        "echo  错误: 依赖安装失败,请检查网络后重新运行本向导",
        "goto end_pause",
        "",
    ]

    # ---------- 可选 1/2: Ollama ----------
    lines += [
        ":step_ollama",
        "echo.",
        "echo ----------------------------------------------",
        "echo  [可选 1/2] Ollama 大模型服务",
        "echo ----------------------------------------------",
        "echo  作用: 在本机运行大模型,把回答总结得更完整自然",
        "echo  不安装: 仍可正常使用 知识库问答 + 联网搜索兜底",
        'if "%AUTO_MODE%"=="1" goto ol_check',
        "",
        'set "ANS="',
        'set /p "ANS=  是否安装 Ollama? [1=安装 / 2=跳过,回车默认跳过]: "',
        'if "%ANS%"=="1" goto ol_check',
        "goto ol_skip",
        "",
        ":ol_check",
        "where ollama >nul 2>&1",
        "if errorlevel 1 goto ol_download",
        "goto ol_already",
        "",
":ol_download",
        "echo  正在下载 Ollama 安装包 [来源 ollama.com 原版],约 200MB...",
        "if exist ollama-installer.exe goto ol_run",
        "curl -L --retry 3 --retry-delay 5 -C - -o ollama-installer.exe --connect-timeout 15 --max-time 3600 https://ollama.com/download/OllamaSetup.exe",
        "if not errorlevel 1 goto ol_run",
        "echo  curl 失败,尝试 PowerShell...",
        "del ollama-installer.exe >nul 2>&1",
        "powershell -NoProfile -ExecutionPolicy Bypass -Command try { Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'ollama-installer.exe' -UseBasicParsing } catch { exit 1 }",
        "if not errorlevel 1 goto ol_run",
        "del ollama-installer.exe >nul 2>&1",
        "goto ol_dl_fail",
        "",
        ":ol_run",
        'if not exist ollama-installer.exe goto ol_dl_fail',
        "echo  正在静默安装 Ollama,可能弹出 UAC 确认...",
        "ollama-installer.exe /S",
        "del ollama-installer.exe >nul 2>&1",
        "echo  等待服务就绪,约 10-15 秒...",
        "ping -n 12 127.0.0.1 >nul",
        "curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1",
        "if errorlevel 1 goto ol_not_running",
        "echo  Ollama 安装并启动成功",
        "goto step_model",
        "",
        ":ol_already",
        "ollama --version",
        "curl -s --max-time 3 http://localhost:11434/api/tags >nul 2>&1",
        "if errorlevel 1 goto ol_not_running",
        "echo  Ollama 已安装且服务在线",
        "goto step_model",
        "",
        ":ol_skip",
        "echo  已跳过 Ollama 安装 [模型下载需要 Ollama,一并跳过]",
        "goto ask_launch",
        "",
        ":ol_not_running",
        "echo  警告: Ollama 已安装但服务未运行",
        "echo  请打开开始菜单 - 搜索 Ollama - 点击运行",
        "goto md_no_ollama",
        "",
        ":ol_dl_fail",
        "echo  错误: Ollama 下载失败,可稍后重试或手动安装:",
        "echo    1. 访问 https://ollama.com/download 下载 OllamaSetup.exe",
        "echo    2. 放到本目录并重命名为 ollama-installer.exe,再运行本向导",
        "goto end_pause",
        "",
    ]

    # ---------- 可选 2/2: 大模型菜单（由 MODELS 自动生成）----------
    lines += [
        ":step_model",
        "echo.",
        "echo ----------------------------------------------",
        "echo  [可选 2/2] 下载大模型 [6 选 1]",
        "echo ----------------------------------------------",
        'if "%AUTO_MODE%"=="1" set "MODEL_TAG=qwen2.5:3b" & goto md_pull',
        "echo  按电脑内存选一个即可,也可跳过,不影响知识库与联网功能:",
    ]
    for i, m in enumerate(MODELS, 1):
        tag_pad = m["tag"].ljust(19)
        lines.append(f"echo   [{i}] {tag_pad} {m['size'].ljust(9)} {m['use']}")
    lines += [
        "echo   [0] 跳过 [回车默认]",
        "",
        'set "MD="',
        'set /p "MD=  请选择 [0-6]: "',
    ]
    for i, m in enumerate(MODELS, 1):
        lines.append(f'if "%MD%"=="{i}" set "MODEL_TAG={m["tag"]}" & goto md_pull')
    lines += [
        "goto md_skip",
        "",
        ":md_pull",
        "echo.",
        f"echo  正在拉取 %MODEL_TAG% ...",
        'ollama list | findstr /I "%MODEL_TAG%" >nul 2>&1',
        "if not errorlevel 1 goto md_exists",
        "echo  下载中,取决于网速约需 3-20 分钟,请勿关闭窗口...",
        "ollama pull %MODEL_TAG%",
        "if errorlevel 1 goto md_pull_fail",
        "echo  模型下载完成,大模型就绪",
        "goto ask_launch",
        "",
        ":md_exists",
        "echo  该模型已存在,无需重复下载",
        "goto ask_launch",
        "",
        ":md_skip",
        "echo  已跳过模型下载 [不装模型也能用: 知识库+联网兜底]",
        "goto ask_launch",
        "",
        ":md_no_ollama",
        "echo  已跳过模型下载 [需先装好并启动 Ollama]",
        "",
        ":md_pull_fail",
        "echo  警告: 模型下载失败 [网络不稳/磁盘不足/Ollama 异常]",
        "echo  可稍后重跑本向导,不影响其他功能",
        "",
    ]

    # ---------- 收尾: 启动询问 ----------
    lines += [
        ":ask_launch",
        "echo.",
        'if "%AUTO_MODE%"=="1" goto do_launch',
        'set "LA="',
        'set /p "LA=  是否立即启动云智? [1=启动,回车默认 / 2=退出]: "',
        'if "%LA%"=="2" goto end_quit',
        "",
        ":do_launch",
        "echo.",
        "echo  正在启动云智... 浏览器将自动打开 http://localhost:5000",
        "echo  关闭本窗口即停止服务",
        "echo.",
        "python app.py",
        "goto end_pause",
        "",
        ":end_quit",
        "echo  向导结束。之后双击根目录 [一键运行.bat] 即可运行云智",
        "",
        ":end_pause",
        "echo.",
        "pause",
        "exit /b",
    ]

    write_bat("一键安装.bat", lines)


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    build_one_click_run()       # 根目录/一键运行.bat —— 唯一入口
    build_unified_installer()   # tools/一键安装.bat —— 安装向导
    build_install_python()      # tools/安装Python.bat
    build_install_ollama()      # tools/安装Ollama.bat
    build_start_only()          # tools/启动.bat
    build_download_sd()         # tools/下载StableDiffusion.bat
    build_install_draw_deps()   # tools/安装画图依赖.bat
    build_install_ocr()         # tools/安装OCR依赖.bat (新增)
    build_install_asr()         # tools/安装语音识别.bat (本地离线 ASR)
    write_sd_downloader()       # tools/_download_sd.py (Python 并发下载器)
    for m in MODELS:
        build_install_model(m)  # tools/安装模型_xxx.bat x6

    print("")
    print("=" * 50)
    print("  bat 文件生成完毕:")
    print("    根目录/一键运行.bat     (普通用户唯一入口)")
    print("    tools/一键安装.bat      (安装向导, /auto 全自动)")
    print("    tools/安装Python.bat    (单独装 Python)")
    print("    tools/安装Ollama.bat    (单独装 Ollama)")
    print("    tools/下载StableDiffusion.bat (单独下载 SD 模型)")
    print("    tools/安装画图依赖.bat  (补装 PyTorch + diffusers)")
    print("    tools/安装语音识别.bat  (装 vosk + 中文模型, 支持 /silent)")
    print(f"    tools/安装模型_xxx.bat  (共 {len(MODELS)} 个)")
    print("=" * 50)
    print("")
    print("普通用户使用流程:")
    print("    双击根目录 [一键运行.bat]: 自动检测环境 + 缺啥补啥 + 启动")
    print("    浏览器访问 http://localhost:5000")
