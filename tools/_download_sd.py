# -*- coding: utf-8 -*-
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
    print(f"共 {len(FILES)} 个文件，并发 4 线程下载\n")

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
