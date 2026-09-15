"""依赖自检脚本：检查必装 + 可选依赖是否就绪"""
import sys
import importlib

REQUIRED = [
    ("flask",          "Flask 后端服务"),
    ("PIL",            "Pillow 图像处理"),
    ("bs4",            "beautifulsoup4 解析"),
    ("matplotlib",     "matplotlib 拓扑/架构图"),
]
SD_OPTIONAL = [
    ("modelscope",       "ModelScope 阿里云镜像（SD 国内最稳源）"),
    ("torch",           "PyTorch"),
    ("diffusers",       "diffusers"),
    ("transformers",    "transformers"),
    ("accelerate",      "accelerate"),
    ("safetensors",     "safetensors"),
    ("huggingface_hub", "huggingface_hub"),
]
OCR_OPTIONAL = [
    ("pytesseract", "pytesseract (OCR)"),
]
ASR_OPTIONAL = [
    ("vosk", "Vosk 本地离线语音识别"),
]

def check(name):
    try:
        m = importlib.import_module(name)
        # 拿版本号
        try:
            from importlib.metadata import version as _v, PackageNotFoundError
            v = _v(name)
        except Exception:
            v = getattr(m, "__version__", "")
        return True, v
    except ImportError as e:
        return False, str(e)

print("=" * 60)
print("云智实训助手 · 环境依赖自检")
print("=" * 60)

# 1. 必装
print("\n[核心必装] 缺一个则启动失败")
core_fail = 0
for name, label in REQUIRED:
    ok, info = check(name)
    mark = "✅" if ok else "❌"
    print(f"  {mark} {name:20s} {label:30s} {'v'+info if ok else info}")
    if not ok: core_fail += 1

# 2. SD 可选
print("\n[可选] SD 插画依赖（缺则降级为拓扑图）")
sd_fail = 0
for name, label in SD_OPTIONAL:
    ok, info = check(name)
    mark = "✅" if ok else "⚠️ "
    print(f"  {mark} {name:20s} {label:30s} {'v'+info if ok else info}")
    if not ok: sd_fail += 1

# 3. OCR 可选
print("\n[可选] OCR 截图识别")
ocr_fail = 0
for name, label in OCR_OPTIONAL:
    ok, info = check(name)
    mark = "✅" if ok else "⚠️ "
    print(f"  {mark} {name:20s} {label:30s} {'v'+info if ok else info}")
    if not ok: ocr_fail += 1

# 3.5 语音识别可选（还要看模型是否下载）
print("\n[可选] 语音识别 ASR（缺则麦克风语音输入不可用，键盘输入不受影响）")
asr_fail = 0
for name, label in ASR_OPTIONAL:
    ok, info = check(name)
    mark = "✅" if ok else "⚠️ "
    print(f"  {mark} {name:20s} {label:30s} {'v'+info if ok else info}")
    if not ok: asr_fail += 1
try:
    import speech_engine
    st = speech_engine.status()
    print(f"  {'✅' if st['ready'] else '⚠️ '} {'模型':20s} {'中文模型 models/vosk':30s} {st['tip']}")
    if not st["ready"]: asr_fail += 1
except Exception as e:
    print(f"  ⚠️  {'模型':20s} 状态查询失败: {e}")

# 4. 模块导入测试
print("\n[模块] 验证所有项目模块可正常 import")
modules = ["qa_engine", "llm_engine", "image_gen_engine", "diagnose_engine",
           "task_engine", "report_engine", "web_search_engine"]
mod_fail = 0
for m in modules:
    try:
        importlib.import_module(m)
        print(f"  ✅ {m}")
    except Exception as e:
        print(f"  ❌ {m}: {e}")
        mod_fail += 1

# 5. 汇总
print("\n" + "=" * 60)
total_fail = core_fail + sd_fail + ocr_fail + asr_fail + mod_fail
if core_fail == 0 and mod_fail == 0:
    print(f"✅ 启动条件满足 (核心 {len(REQUIRED)-core_fail}/{len(REQUIRED)}, 模块 {len(modules)-mod_fail}/{len(modules)})")
    print(f"   可选依赖: SD {len(SD_OPTIONAL)-sd_fail}/{len(SD_OPTIONAL)}, OCR {len(OCR_OPTIONAL)-ocr_fail}/{len(OCR_OPTIONAL)}, 语音 {len(ASR_OPTIONAL)+1-asr_fail}/{len(ASR_OPTIONAL)+1}")
else:
    print(f"❌ {total_fail} 项缺失，请先运行 一键运行.bat 自动补装")
    sys.exit(1)
