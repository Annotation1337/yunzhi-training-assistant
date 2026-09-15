# -*- coding: utf-8 -*-
"""
云智实训助手 · 本地语音识别引擎（Vosk 离线 ASR）
=================================================

职责：
    把学生说的话（普通话）在本地转成文字，供智能问答输入框使用。

数据本地化（对齐项目红线）：
    - 全程离线：音频只在本地内存中处理，识别模型在本地磁盘，
      绝不上传到任何外部服务器。
    - 不使用浏览器自带的 Web Speech API（webkitSpeechRecognition），
      因为 Chrome 的实现会把录音发往国外服务器，违背数据本地化原则。

模型：
    Vosk 中文小模型 vosk-model-small-cn-0.22（约 42MB），
    放在 models/vosk/ 目录下，由「安装语音识别.bat」一键下载。

依赖：
    pip install vosk
    转码建议安装 ffmpeg（处理 webm/opus）；若未装，仅支持 wav 输入。
"""

import json
import os
import shutil
import subprocess
import tempfile
import wave

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models", "vosk")

# Vosk 要求：16kHz 单声道 16bit PCM WAV
TARGET_RATE = 16000
TARGET_CHANNELS = 1

# ============ 关于领域术语识别的说明 ============
# 实测结论（vosk-model-small-cn-0.22，42MB）：
#   - 纯中文句子识别准确率很高，例如"怎么创建云主机和配置安全组"可 100% 命中。
#   - 英文缩写（VPC / Nginx / Docker / K8s 等）容易被识别成音译汉字，
#     例如"什么是VPC和子网的关系"可能识别为"什么是一批诶盒子往的关系"。
#   - 曾尝试用 Vosk 词表（grammar）模式加入云计算热词，结果【严重劣化】：
#     词表模式是封闭语法，只能识别词表内的词，而多数术语不在 small 模型词表中，
#     会把原本正确的识别带偏。故此处【不使用】词表约束，保持开放识别。
# 如需更高术语准确率，可换用更大的中文模型（见 README「语音识别」章节）。


# ---------- 1. 环境与模型状态 ----------
def vosk_available():
    """vosk 库是否已安装"""
    try:
        import vosk  # noqa: F401
        return True
    except Exception:
        return False


def model_ready():
    """模型目录是否存在且有效（含 am/final.mdl 等）"""
    if not os.path.isdir(MODEL_DIR):
        return False
    # Vosk 模型目录特征文件
    for marker in ("am", "conf", "graph"):
        if not os.path.exists(os.path.join(MODEL_DIR, marker)):
            return False
    return True


def status():
    """
    返回语音识别能力状态
    {"installed": bool, "model_ready": bool, "tip": str, "model_dir": str}
    """
    installed = vosk_available()
    ready = model_ready()
    if not installed:
        tip = "未安装 vosk 库，请双击「安装语音识别.bat」一键安装"
    elif not ready:
        tip = "语音模型未下载，请双击「安装语音识别.bat」下载中文模型（约 42MB）"
    else:
        tip = "语音识别就绪（普通话 · 本地离线）"
    return {
        "installed": installed,
        "model_ready": ready,
        "ready": installed and ready,
        "tip": tip,
        "model_dir": MODEL_DIR,
    }


def ffmpeg_available():
    return shutil.which("ffmpeg") is not None


# ---------- 2. 音频转码 ----------
def _to_wav_16k_mono(src_path):
    """
    把任意音频转成 Vosk 需要的 16kHz 单声道 16bit PCM WAV
    优先 ffmpeg；失败时尝试直接读取 wav（若参数已符合则原样返回）
    返回 (wav_path, need_cleanup)
    """
    tmp_out = None

    # 先看是否本来就是合格的 wav
    try:
        with wave.open(src_path, "rb") as wf:
            if (wf.getframerate() == TARGET_RATE
                    and wf.getnchannels() == TARGET_CHANNELS
                    and wf.getsampwidth() == 2):
                return src_path, False
    except Exception:
        pass  # 不是 wav，继续走转码

    if ffmpeg_available():
        tmp_out = src_path + ".16k.wav"
        cmd = [
            "ffmpeg", "-y", "-i", src_path,
            "-ar", str(TARGET_RATE),
            "-ac", str(TARGET_CHANNELS),
            "-sample_fmt", "s16",
            tmp_out,
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=60, check=True)
            if os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 0:
                return tmp_out, True
        except Exception:
            if tmp_out and os.path.exists(tmp_out):
                try:
                    os.remove(tmp_out)
                except Exception:
                    pass
            tmp_out = None

    raise RuntimeError(
        "音频转码失败：未找到 ffmpeg，且输入不是标准 WAV。"
        "请安装 ffmpeg 或改用 WAV 格式录音。"
    )


# ---------- 3. 识别 ----------
def recognize(audio_path):
    """
    本地离线识别普通话语音
    返回 {"ok": bool, "text": str, "tip": str}
    """
    st = status()
    if not st["ready"]:
        return {"ok": False, "text": "", "tip": st["tip"]}

    wav_path, need_cleanup = None, False
    try:
        wav_path, need_cleanup = _to_wav_16k_mono(audio_path)

        from vosk import Model, KaldiRecognizer

        model = Model(MODEL_DIR)
        # 注意：这里【不使用】词表/语法约束模式。
        # 实测：Vosk 传入词表后会变成"封闭语法识别"，只能识别词表内的词，
        #       而云计算术语大多不在 small 模型词表中，会导致识别严重劣化。
        #       开放识别模式下，纯中文准确率很高（实测 100%）。
        rec = KaldiRecognizer(model, TARGET_RATE)
        rec.SetWords(True)

        with wave.open(wav_path, "rb") as wf:
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult() or "{}")
        text = (result.get("text") or "").replace(" ", "").strip()

        if not text:
            return {
                "ok": False,
                "text": "",
                "tip": "没有听清，请靠近麦克风、用普通话清晰地说一遍",
            }
        return {"ok": True, "text": text, "tip": ""}

    except Exception as e:
        return {"ok": False, "text": "", "tip": f"识别失败：{str(e)}"}
    finally:
        if need_cleanup and wav_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass


# ---------- 本地测试 ----------
if __name__ == "__main__":
    print("模型目录:", MODEL_DIR)
    print("状态:", json.dumps(status(), ensure_ascii=False, indent=2))
    print("ffmpeg:", ffmpeg_available())

    # 若模型就绪，用一段测试音频验证
    if status()["ready"]:
        test_wav = os.path.join(BASE_DIR, "models", "test.wav")
        if os.path.exists(test_wav):
            print("\n测试识别:", recognize(test_wav))
        else:
            print("\n（无测试音频，跳过识别测试）")
