# -*- coding: utf-8 -*-
"""
云智实训助手 · Flask 后端
提供静态页面服务 + 智能问答 API 接口

启动：
    python3 app.py
访问：
    http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
import os
import tempfile

from qa_engine import answer as qa_answer
from report_engine import generate_report
from task_engine import answer as task_answer
from diagnose_engine import diagnose, ocr_image, save_upload, ocr_available

# 语音识别（本地离线 Vosk，未安装时功能自动降级，不影响其他模块）
try:
    import speech_engine
except Exception:
    speech_engine = None

app = Flask(__name__, static_folder=None)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============ 静态页面路由 ============
@app.route("/")
def index():
    """主页"""
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    """静态资源（css/js/images/knowledge...）"""
    return send_from_directory(BASE_DIR, filename)


# ============ 问答 API ============
@app.route("/api/ask", methods=["POST"])
def api_ask():
    """
    智能问答接口
    请求：{"question": "你的问题"}
    响应：{"ok": bool, "answer": str, "source": str, "matched": str}
    """
    try:
        data = request.get_json(force=True) or {}
        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "ok": False,
                "answer": "请输入你的问题",
                "source": "",
                "matched": "",
            })

        result = qa_answer(question)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "ok": False,
            "answer": f"服务异常：{str(e)}",
            "source": "",
            "matched": "error",
        }), 500


# ============ 任务引导 API ============
@app.route("/api/task", methods=["POST"])
def api_task():
    """
    任务引导接口
    请求：{"question": "你的问题", "client_id": "学生标识（可选）"}
    响应：{"ok","answer","source","matched","mode","task","step","total"}
    说明：任务流程类问题 → 分步引导；其他问题 → 转智能问答逻辑
    """
    try:
        data = request.get_json(force=True) or {}
        question = data.get("question", "").strip()
        client_id = str(data.get("client_id", "") or "default").strip()[:64] or "default"

        if not question:
            return jsonify({
                "ok": False, "answer": "请输入你的问题", "source": "",
                "matched": "", "mode": "empty", "task": "", "step": 0, "total": 0,
            })

        result = task_answer(question, client_id)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "ok": False,
            "answer": f"服务异常：{str(e)}",
            "source": "", "matched": "error",
            "mode": "error", "task": "", "step": 0, "total": 0,
        }), 500


# ============ 排错诊断 API ============
@app.route("/api/diagnose", methods=["POST"])
def api_diagnose():
    """
    排错诊断接口
    请求：{"text": "错误日志或故障描述"}
    响应：{"ok","answer","source","matched","mode","rule"}
    """
    try:
        data = request.get_json(force=True) or {}
        text = data.get("text", "").strip()
        result = diagnose(text)
        status = 200 if result.get("ok") else 400
        return jsonify(result), status
    except Exception as e:
        return jsonify({
            "ok": False, "answer": f"服务异常：{str(e)}",
            "source": "", "matched": "error", "mode": "error", "rule": "",
        }), 500


@app.route("/api/ocr", methods=["POST"])
def api_ocr():
    """
    截图识别接口（可选功能，需本机安装 Tesseract）
    请求：multipart/form-data，字段 image
    响应：{"ok","text","answer","lang"}
    """
    try:
        if "image" not in request.files:
            return jsonify({"ok": False, "text": "", "answer": "未收到图片", "lang": ""}), 400

        file = request.files["image"]
        if not file or not file.filename:
            return jsonify({"ok": False, "text": "", "answer": "未选择图片", "lang": ""}), 400

        path, err = save_upload(file, file.filename)
        if err:
            return jsonify({"ok": False, "text": "", "answer": err, "lang": ""}), 400

        result = ocr_image(path)
        result["file"] = os.path.basename(path)
        return jsonify(result)

    except Exception as e:
        return jsonify({"ok": False, "text": "", "answer": f"服务异常：{str(e)}", "lang": ""}), 500


# ============ 语音识别 API（本地离线 · 普通话）============
@app.route("/api/speech/status")
def api_speech_status():
    """
    语音识别能力状态
    响应：{"ready": bool, "installed": bool, "model_ready": bool, "tip": str}
    说明：全程本地离线，音频不外发（数据绝对本地化）
    """
    try:
        if speech_engine is None:
            return jsonify({
                "ready": False, "installed": False, "model_ready": False,
                "tip": "语音模块未加载，请双击「安装语音识别.bat」",
            })
        return jsonify(speech_engine.status())
    except Exception as e:
        return jsonify({
            "ready": False, "installed": False, "model_ready": False,
            "tip": f"语音状态查询失败：{str(e)}",
        })


@app.route("/api/speech/recognize", methods=["POST"])
def api_speech_recognize():
    """
    本地离线语音转文字（仅普通话）
    请求：multipart/form-data，字段 audio（webm/wav/mp3 等）
    响应：{"ok": bool, "text": str, "tip": str}
    说明：音频仅在本机内存中处理，识别后立即删除，绝不上传外发
    """
    tmp_path = None
    try:
        if speech_engine is None:
            return jsonify({
                "ok": False, "text": "",
                "tip": "语音模块未加载，请双击「安装语音识别.bat」安装",
            })

        if "audio" not in request.files:
            return jsonify({"ok": False, "text": "", "tip": "未收到音频数据"}), 400

        file = request.files["audio"]
        if not file or not file.filename:
            return jsonify({"ok": False, "text": "", "tip": "未选择音频文件"}), 400

        # 先查状态，模型未就绪时直接给出明确指引（避免无谓等待）
        st = speech_engine.status()
        if not st["ready"]:
            return jsonify({"ok": False, "text": "", "tip": st["tip"]})

        # 音频写入临时文件（识别后即删，减少本地数据留存）
        suffix = os.path.splitext(file.filename)[1].lower() or ".webm"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="yz_asr_")
        os.close(fd)
        file.save(tmp_path)

        result = speech_engine.recognize(tmp_path)
        return jsonify(result)

    except Exception as e:
        return jsonify({"ok": False, "text": "", "tip": f"服务异常：{str(e)}"}), 500
    finally:
        # 无论成功失败，都清理临时音频（数据本地化：不留存录音）
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# ============ 报告生成 API ============
@app.route("/api/report", methods=["POST"])
def api_report():
    """
    一键生成实训报告框架
    请求：{"topic","learned","problems","solutions","guidance","feelings"}
    响应：{"ok": bool, "report_html": str, "answer": str}
    """
    try:
        data = request.get_json(force=True) or {}
        result = generate_report(data)
        status = 200 if result.get("ok") else 400
        return jsonify(result), status

    except Exception as e:
        return jsonify({
            "ok": False,
            "report_html": "",
            "answer": f"服务异常：{str(e)}",
        }), 500


# ============ 本地大模型状态 ============
@app.route("/api/llm_status")
def llm_status():
    """
    返回本地大模型（Ollama）与联网兜底的连接状态
    响应：{"available": bool, "model": str, "installed": bool, "models": [...],
           "host": str, "web_search": bool}
    """
    try:
        import llm_engine
        import web_search_engine
        ok, info = llm_engine.check_available()
        models = info.get("models", []) if ok else []
        return jsonify({
            "available": ok,
            "model": llm_engine.get_active_model(),
            "installed": llm_engine.model_installed() if ok else False,
            "models": models,
            "host": llm_engine.OLLAMA_HOST,
            "web_search": web_search_engine.ENABLE_WEB_SEARCH,
        })
    except Exception as e:
        return jsonify({
            "available": False, "model": "", "installed": False,
            "models": [], "host": "", "web_search": False, "error": str(e),
        })


# ============ 聊天模式切换（侧边栏按钮）============
@app.route("/api/mode")
def get_mode():
    """返回当前聊天响应模式（loose=宽松 / strict=严格）"""
    try:
        import qa_engine
        return jsonify({"mode": qa_engine.RESPONSE_MODE})
    except Exception as e:
        return jsonify({"mode": "loose", "error": str(e)})


# ============ 依赖检测（侧边栏状态展示 / 故障排查）============
@app.route("/api/dependencies")
def dependencies_status():
    """扫描所有第三方依赖，返回安装状态。
    前端可在「侧边栏」或「故障排查」处展示，让学生一眼看到哪些没装。
    """
    deps = {
        # 必装：核心功能
        "flask":           {"required": True,  "label": "Flask 后端服务",     "category": "core"},
        "PIL":             {"required": True,  "label": "Pillow 图像处理",    "category": "core"},
        "bs4":             {"required": True,  "label": "beautifulsoup4 解析", "category": "core"},
        "matplotlib":      {"required": True,  "label": "matplotlib 拓扑图",  "category": "core"},
        # 可选：SD 画图
        "modelscope":       {"required": False, "label": "ModelScope (阿里云)", "category": "sd"},
        "torch":           {"required": False, "label": "PyTorch",            "category": "sd"},
        "diffusers":       {"required": False, "label": "diffusers",          "category": "sd"},
        "transformers":    {"required": False, "label": "transformers",       "category": "sd"},
        "accelerate":      {"required": False, "label": "accelerate",         "category": "sd"},
        "safetensors":     {"required": False, "label": "safetensors",        "category": "sd"},
        "huggingface_hub": {"required": False, "label": "huggingface_hub",    "category": "sd"},
        # 可选：OCR
        "pytesseract":     {"required": False, "label": "pytesseract (OCR)",  "category": "ocr"},
    }
    out = {}
    for mod_name, meta in deps.items():
        try:
            m = __import__(mod_name)
            # 用 importlib.metadata 拿版本（兼容 Flask 3.2+ 移除 __version__）
            ver = ""
            try:
                from importlib.metadata import version as _v, PackageNotFoundError as _PNF
                ver = _v(mod_name)
            except Exception:
                ver = getattr(m, "__version__", "") or ""
            out[mod_name] = {"ok": True, "version": ver, **meta}
        except ImportError as e:
            out[mod_name] = {"ok": False, "version": "", "error": str(e), **meta}

    # 汇总统计
    core_missing = [k for k, v in out.items() if v["required"] and not v["ok"]]
    sd_missing = [k for k, v in out.items() if v["category"] == "sd" and not v["ok"]]
    ocr_missing = [k for k, v in out.items() if v["category"] == "ocr" and not v["ok"]]
    return jsonify({
        "deps": out,
        "core_missing": core_missing,
        "sd_missing": sd_missing,
        "ocr_missing": ocr_missing,
        "summary": {
            "core_ok": len(core_missing) == 0,
            "sd_ok": len(sd_missing) == 0,
            "ocr_ok": len(ocr_missing) == 0,
        }
    })


@app.route("/api/mode/set", methods=["POST"])
def set_mode_api():
    """切换聊天响应模式。请求体: {"mode": "loose"|"strict"}
    返回: {"ok": bool, "mode": str, "answer": str}  answer 为可显示的提示文案
    """
    try:
        data = request.get_json(silent=True) or {}
        new_mode = (data.get("mode") or "").lower().strip()
        if new_mode not in ("loose", "strict"):
            return jsonify({"ok": False, "error": "mode 必须是 loose 或 strict"}), 400
        import qa_engine
        old_mode = qa_engine.RESPONSE_MODE
        qa_engine.RESPONSE_MODE = new_mode
        if new_mode == "strict":
            msg = ("✅ 已切换到 <strong>严格模式</strong>：只回答云计算/实训相关问题，"
                   "其他话题一律拒绝。需要恢复请说「宽松模式」。")
        else:
            msg = ("✅ 已切换到 <strong>宽松模式</strong>：非硬违规的话题都能聊，"
                   "生活/娱乐类我会礼貌拐回云知识。需要收紧请说「严格模式」。")
        return jsonify({"ok": True, "mode": new_mode, "prev": old_mode, "answer": msg})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ============ 知识库管理 API ============
@app.route("/api/kb/list")
def kb_list():
    """列出某库条目(带摘要+搜索)。参数: type=qa|task|trouble, kw=搜索词"""
    import kb_engine
    kb_type = request.args.get("type", "qa")
    kw = request.args.get("kw", "")
    return jsonify(kb_engine.list_items(kb_type, kw))


@app.route("/api/kb/item")
def kb_item():
    """取单条完整内容。参数: type, id"""
    import kb_engine
    return jsonify(kb_engine.get_item(
        request.args.get("type", "qa"), request.args.get("id", "")))


@app.route("/api/kb/save", methods=["POST"])
def kb_save():
    """新增或更新一条。请求体: {"type": "qa", "item": {...}}
    item 含 id → 更新;不含 id → 新增(自动生成)"""
    import kb_engine
    data = request.get_json(silent=True) or {}
    kb_type = data.get("type", "")
    item = data.get("item") or {}
    if kb_type not in kb_engine.KB_TYPES:
        return jsonify({"ok": False, "error": f"未知库类型 {kb_type}"}), 400
    # 基本校验:至少要有可检索的内容
    if not item.get("keywords") and not item.get("name"):
        return jsonify({"ok": False, "error": "至少填写关键词或名称"}), 400
    return jsonify(kb_engine.save_item(kb_type, item))


@app.route("/api/kb/delete", methods=["POST"])
def kb_delete():
    """删除一条(自动备份)。请求体: {"type": "qa", "id": "xxx"}"""
    import kb_engine
    data = request.get_json(silent=True) or {}
    return jsonify(kb_engine.delete_item(
        data.get("type", ""), data.get("id", "")))


@app.route("/api/kb/export")
def kb_export():
    """导出全部知识库为 zip 下载"""
    import kb_engine
    r = kb_engine.export_all()
    if not r.get("ok"):
        return jsonify(r), 500
    from flask import send_file
    return send_file(r["zip"], as_attachment=True, download_name=r["name"],
                     mimetype="application/zip")


@app.route("/api/kb/import", methods=["POST"])
def kb_import():
    """导入 json 或 zip(自动备份;merge=1 合并/0 覆盖)"""
    import kb_engine
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "未收到文件"}), 400
    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "未选择文件"}), 400
    merge = request.form.get("merge", "1") != "0"
    return jsonify(kb_engine.import_data(f.stream, f.filename, merge=merge))


@app.route("/api/kb/docs")
def kb_docs():
    """列出 markdown 教材(只读)"""
    import kb_engine
    return jsonify(kb_engine.list_docs())


@app.route("/api/kb/doc")
def kb_doc():
    """读一篇 markdown 教材。参数: path=相对路径"""
    import kb_engine
    return jsonify(kb_engine.get_doc(request.args.get("path", "")))


# ============ 出图接口 ============
@app.route("/api/image_gen", methods=["POST"])
def api_image_gen():
    """调 image_gen_engine 出图（拓扑自动 matplotlib；插画 SD 本地推理）"""
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    img_type = data.get("type", "auto")  # auto / topology / illustration
    width = int(data.get("width") or 512)
    height = int(data.get("height") or 512)
    if not prompt:
        return jsonify({"ok": False, "error": "prompt 不能为空"})
    try:
        import image_gen_engine as ige
        r = ige.generate(prompt, type=img_type, width=width, height=height)
        return jsonify(r)
    except Exception as e:
        return jsonify({"ok": False, "error": f"出图引擎异常: {e}"})


@app.route("/api/sd_status")
def sd_status():
    """返回 SD 模型状态：是否就绪、CUDA、下载源等"""
    try:
        import image_gen_engine as ige
        return jsonify(ige.get_status())
    except Exception as e:
        return jsonify({"ready": False, "error": str(e)})


# ============ 健康检查 ============
@app.route("/api/health")
def health():
    llm = "离线"
    llm_model = ""
    try:
        import llm_engine
        ok, _ = llm_engine.check_available()
        llm = "在线" if ok else "离线"
        llm_model = llm_engine.get_active_model()
    except Exception:
        pass
    return jsonify({
        "status": "ok",
        "service": "云智实训助手",
        "llm": llm,
        "llm_model": llm_model,
    })


if __name__ == "__main__":
    print("=" * 52)
    print("   云智实训助手 · 后端服务启动中...")
    print("=" * 52)
    print()
    print("   请在浏览器中访问：")
    print()
    print("       >>>  http://localhost:5000  <<<")
    print()
    print("   问答接口: POST http://localhost:5000/api/ask")
    print("   任务接口: POST http://localhost:5000/api/task")
    print("   排错接口: POST http://localhost:5000/api/diagnose")
    print("   截图识别: POST http://localhost:5000/api/ocr")
    print("   报告接口: POST http://localhost:5000/api/report")
    print("   语音识别: POST http://localhost:5000/api/speech/recognize")
    print("   语音状态: GET  http://localhost:5000/api/speech/status")

    # 本地大模型（Ollama）状态检测
    try:
        import llm_engine
        ok, info = llm_engine.check_available()
        if ok:
            active = llm_engine.get_active_model()
            installed = llm_engine.model_installed()
            models_str = ",".join(info.get("models", [])) or "（无）"
            if installed:
                print(f"   本地大模型(Ollama): 在线 | 模型 {active}")
            else:
                # Ollama 在线但默认模型未装 → 提示用户拉取
                print(f"   本地大模型(Ollama): 在线 | 但默认模型 {llm_engine.OLLAMA_MODEL} 未安装")
                print(f"      本机已装模型: {models_str}")
                print(f"      正在自动切换到: {active}（系统会自动选已装的模型）")
                print(f"      若想使用 qwen2.5:3b，请运行: ollama pull qwen2.5:3b")
        else:
            print(f"   本地大模型(Ollama): 离线（未检测到 {llm_engine.OLLAMA_HOST}，"
                  "请确认 Ollama 已启动;不影响知识库问答）")
    except Exception as e:
        print(f"   本地大模型(Ollama): 状态检测异常 ({type(e).__name__}: {e})，"
              "不影响知识库问答")

    print("   截图识别(OCR): " + ("已启用" if ocr_available() else "未安装 Tesseract，仅支持文字描述"))

    # 语音识别（本地离线 Vosk · 普通话）
    try:
        if speech_engine is None:
            print("   语音识别(ASR): 模块未加载，不影响其他功能")
        else:
            st = speech_engine.status()
            print("   语音识别(ASR): " + ("已启用（普通话 · 本地离线）" if st["ready"] else st["tip"]))
    except Exception:
        print("   语音识别(ASR): 状态检测异常，不影响其他功能")

    print("   停止服务: 按 Ctrl + C，或直接关闭窗口")
    print("=" * 52)
    print()

    # Windows 下自动打开浏览器（避免手动输入网址）
    import threading
    import webbrowser

    def open_browser():
        import time
        time.sleep(1.5)
        url = "http://localhost:5000"
        # 方式一：标准 webbrowser
        try:
            if webbrowser.open(url):
                return
        except Exception:
            pass
        # 方式二：Windows 原生 startfile（webbrowser 失效时兜底）
        try:
            import os
            os.startfile(url)  # type: ignore
        except Exception:
            pass

    # 仅在本地运行时自动打开（避免服务器环境重复打开）
    threading.Thread(target=open_browser, daemon=True).start()

    app.run(host="127.0.0.1", port=5000, debug=False)
