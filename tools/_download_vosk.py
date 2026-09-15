# -*- coding: utf-8 -*-
"""
云智实训助手 · 中文语音识别模型下载器（Vosk）
=============================================

下载 vosk-model-small-cn-0.22（约 42MB，解压后约 66MB），
解压到 models/vosk/ 目录，供 speech_engine.py 使用。

下载策略（三级回退）：
    1. alphacephei.com 官方源（直连 zip，支持断点续传）
    2. hf-mirror.com 国内镜像（HuggingFace 镜像，需 huggingface_hub）
    3. huggingface.co 原版（最后兜底）

运行：
    python tools/_download_vosk.py
"""

import os
import sys
import zipfile
import urllib.request

MODEL_NAME = "vosk-model-small-cn-0.22"
ZIP_URLS = [
    "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip",
    "https://hf-mirror.com/alphacep/vosk-model-small-cn-0.22/resolve/main/model.zip",
    "https://huggingface.co/alphacep/vosk-model-small-cn-0.22/resolve/main/model.zip",
]
HF_REPO = "alphacep/vosk-model-small-cn-0.22"

# 本文件在 tools/ 下，模型放到 项目根/models/vosk
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(BASE_DIR, "models", "vosk")
TMP_ZIP = os.path.join(BASE_DIR, "models", MODEL_NAME + ".zip")


def _progress(block_num, block_size, total_size):
    """简单的下载进度显示"""
    if total_size <= 0:
        return
    done = block_num * block_size
    pct = min(100, int(done * 100 / total_size))
    mb = done / 1024 / 1024
    total_mb = total_size / 1024 / 1024
    if block_num % 50 == 0 or pct == 100:
        sys.stdout.write(f"\r  已下载 {pct}%  ({mb:.1f} MB / {total_mb:.1f} MB)")
        sys.stdout.flush()


def download_zip():
    """依次尝试各源下载 zip，成功返回本地路径"""
    os.makedirs(os.path.dirname(TMP_ZIP), exist_ok=True)
    for i, url in enumerate(ZIP_URLS, 1):
        label = ["官方源", "国内镜像 hf-mirror", "原版 huggingface"][i - 1]
        print(f"  尝试 [{i}/3] {label}: {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(TMP_ZIP, "wb") as f:
                total = int(resp.headers.get("Content-Length") or 0)
                block = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    block += 1
                    _progress(block, 65536, total)
            print()
            if os.path.getsize(TMP_ZIP) > 5 * 1024 * 1024:
                print(f"  下载完成: {os.path.getsize(TMP_ZIP) / 1024 / 1024:.1f} MB")
                return TMP_ZIP
            print("  文件过小，疑似下载失败，换下一个源")
            os.remove(TMP_ZIP)
        except Exception as e:
            print(f"  失败: {type(e).__name__}: {e}")
            if os.path.exists(TMP_ZIP):
                try:
                    os.remove(TMP_ZIP)
                except Exception:
                    pass
    return None


def download_via_hf():
    """回退：用 huggingface_hub 拉取整个仓库（国内走 hf-mirror）"""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("  未安装 huggingface_hub，跳过该方式")
        return False
    for endpoint in ["https://hf-mirror.com", None]:
        label = "国内镜像 hf-mirror" if endpoint else "原版 huggingface"
        print(f"  尝试 {label} 拉取仓库 {HF_REPO} ...")
        try:
            if endpoint:
                os.environ["HF_ENDPOINT"] = endpoint
            else:
                os.environ.pop("HF_ENDPOINT", None)
            path = snapshot_download(repo_id=HF_REPO, local_dir=TARGET_DIR)
            print(f"  完成: {path}")
            return True
        except Exception as e:
            print(f"  失败: {type(e).__name__}: {e}")
    return False


def extract(zip_path):
    """解压并把模型文件规整到 models/vosk/ 根目录"""
    print("  正在解压，请稍候...")
    tmp_dir = os.path.join(BASE_DIR, "models", "_vosk_tmp")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(tmp_dir)

    # zip 内通常是 vosk-model-small-cn-0.22/ 一层目录，找到含 am/conf/graph 的那层
    root = tmp_dir
    for dirpath, dirnames, _ in os.walk(tmp_dir):
        if all(os.path.isdir(os.path.join(dirpath, d)) for d in ("am", "conf", "graph")):
            root = dirpath
            break

    os.makedirs(TARGET_DIR, exist_ok=True)
    import shutil
    for name in os.listdir(root):
        s = os.path.join(root, name)
        d = os.path.join(TARGET_DIR, name)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"  模型已就位: {TARGET_DIR}")
    return True


def verify():
    if not os.path.isdir(TARGET_DIR):
        return False
    return all(os.path.exists(os.path.join(TARGET_DIR, d)) for d in ("am", "conf", "graph"))


def main():
    print("=" * 52)
    print("  云智 · 中文语音识别模型下载（Vosk 离线 ASR）")
    print(f"  模型: {MODEL_NAME}  约 42MB")
    print(f"  目标: {TARGET_DIR}")
    print("=" * 52)

    if verify():
        print("  模型已存在，无需重复下载。")
        print("  如需重装，请删除 models/vosk 目录后重跑本脚本。")
        return 0

    zip_path = download_zip()
    if zip_path:
        extract(zip_path)
        try:
            os.remove(zip_path)
        except Exception:
            pass
    else:
        print("  直连 zip 全部失败，改用 HuggingFace 方式...")
        if not download_via_hf():
            print()
            print("  [失败] 所有下载源均不可用。")
            print("  手动方案：浏览器打开下面任一地址，下载 zip 后解压到 models/vosk/")
            for u in ZIP_URLS:
                print("    " + u)
            return 1

    if verify():
        print()
        print("  [成功] 语音识别模型就绪！")
        print("  接下来：双击根目录 一键运行.bat，进入智能问答页点麦克风即可说话。")
        return 0

    print("  [警告] 解压后未检测到完整模型文件，请检查 models/vosk 目录。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
