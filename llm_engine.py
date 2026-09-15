# -*- coding: utf-8 -*-
"""
云智实训助手 · 本地大模型引擎（Ollama + RAG + 联网兜底）
========================================================

职责（竞赛版三级链路）：
    1. 知识库命中 → 上层直接返回知识库答案（本模块不参与）
    2. 知识库未命中但检索到相关片段（达到阈值）→ RAG：片段交 Ollama 生成
    3. 知识库确实没有 → 上层调用 web_search_engine 联网检索，
       本模块把网络片段作为上下文交 Ollama 总结（answer_with_web_context）
    - 注入 / 范围外 → 上层在调用前已拒绝，本模块不处理

原则：
    - 知识库优先：只有知识库确实没有的内容才允许联网补充
    - 可溯源：联网回答必须列出来源 URL；RAG 回答标注知识库来源
    - 诚实边界：上下文不足时明确告知，不编造命令/参数

配置（环境变量，均有默认值）：
    OLLAMA_HOST   Ollama 服务地址，默认 http://localhost:11434
    OLLAMA_MODEL  模型名，默认 qwen2.5:3b
    OLLAMA_TIMEOUT 请求超时秒数，默认 120
    RAG_MIN_SCORE   知识库相关度最低分（低于视为知识库未收录），默认 4
"""

import json
import os
import re
import urllib.request
import urllib.error

# ---------- 配置 ----------
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
# 默认首选模型；若未显式指定 OLLAMA_MODEL，且该模型未安装，会自动切换到本机已装模型
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))
# RAG 检索最低相关度：低于该分数视为「知识库未收录」，允许联网兜底
RAG_MIN_SCORE = int(os.environ.get("RAG_MIN_SCORE", "4"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QA_DATA_PATH = os.path.join(BASE_DIR, "knowledge", "qa_data.json")
TASK_DATA_PATH = os.path.join(BASE_DIR, "knowledge", "task_data.json")
TROUBLE_DATA_PATH = os.path.join(BASE_DIR, "knowledge", "trouble_data.json")

# 回答末尾固定的溯源说明
RAG_SOURCE_NOTE = "（以上回答由本地大模型基于实训知识库生成，供参考）"

# 运行时实际使用的模型（自动探测缓存）
_active_model = None
# 最近一次 generate 失败的原因（供上层精准提示）
_last_generate_error = ""


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ---------- 1. Ollama 连接与调用 ----------
def check_available():
    """检测 Ollama 是否在线，返回 (bool, info_dict)"""
    try:
        req = urllib.request.Request(
            OLLAMA_HOST + "/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", [])]
        return True, {"models": models}
    except Exception as e:
        return False, {"error": str(e)}


def model_installed(model=None):
    """检查指定模型是否已拉取；不传参时检查"实际可用模型"（含自动探测）"""
    if model is None:
        # 不指定时：只要本机有任意可用模型即算就绪
        ok, info = check_available()
        if not ok:
            return False
        return bool(info.get("models"))
    ok, info = check_available()
    if not ok:
        return False
    return any(m == model or m.startswith(model + ":") for m in info.get("models", []))


def _pick_available_model():
    """在 OLLAMA_MODEL 未安装时，自动挑选本机已装的一个模型。
    优先级：qwen2.5 系列 → 任意 qwen → 任意已装模型。
    返回模型名，若一个都没装则返回 None。"""
    ok, info = check_available()
    if not ok:
        return None
    models = info.get("models", [])
    if not models:
        return None

    # 1) 优先 qwen2.5 系列
    for m in models:
        if m.startswith("qwen2.5"):
            return m
    # 2) 任意 qwen
    for m in models:
        if "qwen" in m:
            return m
    # 3) 兜底：第一个已装模型
    return models[0]


def get_active_model():
    """返回当前实际可用的模型名。
    - OLLAMA_MODEL 已安装 → 用它
    - 否则自动挑选本机已装模型（并缓存）
    - 都没装 → 返回 OLLAMA_MODEL（保持原样，调用时自然失败并降级）
    """
    global _active_model
    if _active_model:
        return _active_model

    ok, info = check_available()
    if not ok:
        return OLLAMA_MODEL
    models = info.get("models", [])
    if any(m == OLLAMA_MODEL or m.startswith(OLLAMA_MODEL + ":") for m in models):
        _active_model = OLLAMA_MODEL
        return _active_model

    picked = _pick_available_model()
    if picked:
        _active_model = picked
        return _active_model
    return OLLAMA_MODEL


def generate(prompt, system="", model=None, timeout=None):
    """
    调用 Ollama /api/chat 生成回答（非流式）
    返回 str 或 None（失败时返回 None）

    失败时通过 _last_generate_error 记录具体原因，便于上层排错与精准提示
    """
    global _last_generate_error
    _last_generate_error = ""
    model = model or get_active_model()
    timeout = timeout or OLLAMA_TIMEOUT
    payload = {
        "model": model,
        "stream": False,
        "messages": [],
    }
    if system:
        payload["messages"].append({"role": "system", "content": system})
    payload["messages"].append({"role": "user", "content": prompt})

    try:
        req = urllib.request.Request(
            OLLAMA_HOST + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data.get("message", {}).get("content", "").strip()
        if not content:
            _last_generate_error = "Ollama 返回空内容（模型可能没加载完成）"
            return None
        return content
    except urllib.error.URLError as e:
        _last_generate_error = f"无法连接 Ollama ({OLLAMA_HOST}): {e.reason}"
        return None
    except Exception as e:
        _last_generate_error = f"{type(e).__name__}: {e}"
        return None


def get_last_error():
    """返回最近一次 generate() 失败的具体原因（供上层精准提示）"""
    return _last_generate_error


# ---------- 2. RAG 检索 ----------
def _flatten_candidates():
    """
    把三类知识库展开为「文本片段」列表，每条含 title/text/source
    用于 RAG 检索
    """
    candidates = []

    qa = _load_json(QA_DATA_PATH)
    if qa:
        for item in qa.get("qa_list", []):
            text = re.sub(r"<[^>]+>", "", item.get("answer", ""))
            text = text.replace("&nbsp;", " ").replace("&amp;", "&")
            candidates.append({
                "title": item.get("id", ""),
                "text": text,
                "source": item.get("source", "实训知识库"),
                "type": "问答",
            })

    task = _load_json(TASK_DATA_PATH)
    if task:
        for item in task.get("tasks", []):
            parts = [item.get("name", ""), item.get("goal", "")]
            for st in item.get("steps", []):
                parts.append(st.get("title", "") + " " + st.get("detail", ""))
            candidates.append({
                "title": item.get("name", ""),
                "text": " ".join(parts),
                "source": item.get("source", "实训任务书"),
                "type": "任务",
            })

    trouble = _load_json(TROUBLE_DATA_PATH)
    if trouble:
        for rule in trouble.get("rules", []):
            parts = [rule.get("name", ""), rule.get("symptom", ""),
                     rule.get("cause", ""), rule.get("solution", "")]
            candidates.append({
                "title": rule.get("name", ""),
                "text": " ".join(parts),
                "source": "排错知识库",
                "type": "排错",
            })

    return candidates


def retrieve(question, top_k=3, min_score=None):
    """
    检索与问题最相关的知识库片段
    min_score：最低相关度（默认取 RAG_MIN_SCORE），低于该值的片段视为无关丢弃
    返回：[{title, text, source, type, score}] 按相关度降序
    """
    min_score = RAG_MIN_SCORE if min_score is None else min_score
    candidates = _flatten_candidates()
    q = question.lower()

    # 简单相关性打分：关键词命中次数 + 命中关键词长度
    scored = []
    q_terms = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", q)

    for c in candidates:
        text_low = c["text"].lower()
        score = 0.0
        hit_count = 0
        for term in q_terms:
            if term in text_low:
                hit_count += 1
                score += len(term)
        if hit_count > 0:
            score += hit_count * 2  # 命中多个词加分
        if score >= min_score:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def build_context(results):
    """把检索结果拼成给模型的上下文"""
    if not results:
        return ""
    parts = []
    for i, r in enumerate(results, 1):
        parts.append(f"【参考片段{i}｜{r['type']}｜来源：{r['source']}】\n{r['text']}")
    return "\n\n".join(parts)


# ---------- 3. 安全约束 system prompt ----------
SYSTEM_PROMPT = (
    "你是「云智」，一位部署在高职云计算实训课堂的本地化 AI 助教。\n"
    "请严格遵循以下规则回答学生问题：\n"
    "1. 知识库优先：只能依据下面提供的【参考片段】作答，"
    "不要使用你自身的通用知识编造命令、参数或配置。\n"
    "2. 诚实边界：如果参考片段不足以回答，直接说「当前知识库暂未收录该问题」，"
    "并建议向现场指导教师求助，绝不杜撰。\n"
    "3. 教育导向：回答要结论先行、分点清晰，适当解释原理，"
    "面向高职学生、用通俗语言。\n"
    "4. 内容合规：只讨论云计算实训相关内容，不回答无关或敏感话题。\n"
    "5. 输出格式：使用 Markdown，命令用代码块，步骤用有序列表。"
)


def rag_answer(question):
    """
    RAG 增强兜底：检索 + 生成
    返回 {"ok": bool, "answer": str, "source": str, "matched": str,
          "reason": str}   # reason: "" / "no_context"(知识库无相关内容) / "model_down"(模型不可用)
    """
    # 检索（带阈值：低于阈值视为知识库未收录）
    results = retrieve(question, top_k=3)
    context = build_context(results)

    if not context:
        return {
            "ok": False,
            "answer": "当前知识库暂未收录该问题，建议向现场指导教师求助。",
            "source": "",
            "matched": "",
            "reason": "no_context",
        }

    # 组装 prompt
    prompt = (
        f"学生问题：{question}\n\n"
        f"以下是本地实训知识库中检索到的参考片段：\n{context}\n\n"
        f"请依据以上片段，用简洁的中文回答学生的问题。"
    )

    answer_text = generate(prompt, system=SYSTEM_PROMPT)

    if not answer_text:
        # LLM 不可用 → 降级为提示（reason 供上层决定是否联网兜底）
        # 显示真实失败原因，避免误判为「未安装 Ollama」
        err = get_last_error() or "未知原因"
        return {
            "ok": False,
            "answer": (f"本地大模型调用失败（{err}）。\n"
                       f"• 如果已启动 Ollama，请确认 {OLLAMA_HOST} 可访问\n"
                       f"• 已装模型：{get_active_model()}\n"
                       f"• 当前知识库暂未直接收录该问题，建议向现场指导教师求助。"),
            "source": "",
            "matched": "",
            "reason": "model_down",
        }

    # 溯源
    sources = "、".join(sorted(set(r["source"] for r in results if r.get("source"))))
    return {
        "ok": True,
        "answer": answer_text + "\n\n" + RAG_SOURCE_NOTE,
        "source": sources or "本地知识库",
        "matched": "llm",
        "reason": "",
    }


# ---------- 4. 联网兜底：基于网络检索片段生成回答 ----------
WEB_SYSTEM_PROMPT = (
    "你是「云智」，一位部署在高职云计算实训课堂的本地化 AI 助教。\n"
    "本次知识库未收录学生的问题，以下回答基于【网络检索片段】（来自互联网公开资料）。\n"
    "请严格遵循以下规则：\n"
    "1. 只依据提供的【网络检索片段】作答，片段之间冲突时优先采用更权威来源"
    "（如官方文档 > 教程网站）；片段不足以回答时明确说明。\n"
    "2. 结论先行、分点清晰、面向高职学生用通俗语言，适当解释原理。\n"
    "3. 引用来源：在关键结论后标注（来源[编号]），编号对应片段序号。\n"
    "4. 只讨论云计算实训相关内容，不输出任何无关或敏感内容。\n"
    "5. 输出格式：使用 Markdown，命令用代码块，步骤用有序列表，不要输出 HTML 标签。"
)

WEB_SOURCE_NOTE = ("（以上回答由本地大模型基于互联网检索结果生成，"
                   "如与课堂教材冲突，请以教材和指导教师为准）")


def md_to_html(text):
    """
    把模型输出的 Markdown 粗略转换为前端可渲染的 HTML
    （前端聊天气泡使用 innerHTML，不解析 Markdown）
    支持：```代码块```、**加粗**、[文本](链接)、换行；并移除 <script> 防注入
    """
    if not text:
        return ""
    text = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", text,
                  flags=re.IGNORECASE | re.DOTALL)
    # 代码块
    def _code(m):
        body = m.group(1).strip()
        body = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<pre style='background:#0f172a;color:#e2e8f0;padding:10px 12px;border-radius:8px;overflow-x:auto;font-size:13px;margin:8px 0;'><code>{body}</code></pre>"
    text = re.sub(r"```[a-zA-Z0-9]*\n?(.*?)```", _code, text, flags=re.DOTALL)
    # 行内代码
    text = re.sub(r"`([^`\n]+)`",
                  r"<code style='background:#eef2ff;color:#3730a3;padding:1px 5px;border-radius:4px;'>\1</code>",
                  text)
    # 加粗
    text = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", text)
    # 链接 [t](u) → 可点链接（新窗口打开）
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                  r"<a href='\2' target='_blank' rel='noopener noreferrer' "
                  r"style='color:#2563eb;word-break:break-all;'>\1</a>", text)
    # 换行
    text = text.replace("\n", "<br>")
    return text.strip()


def answer_with_web_context(question, web_results):
    """
    联网兜底回答：把网络检索片段作为上下文交 Ollama 总结
    参数：
        question     学生原始问题
        web_results  web_search_engine.search() 的结果列表
    返回 {"ok": bool, "answer": str, "source": str, "matched": str}
        ok=False 表示 Ollama 不可用（上层可直接罗列搜索结果降级）
    """
    context = ""
    for i, r in enumerate(web_results, 1):
        context += (f"【网络检索片段{i}｜来源：{r.get('title','')}｜URL：{r.get('url','')}】\n"
                    f"{r.get('snippet','')}\n\n")

    prompt = (
        f"学生问题：{question}\n\n"
        f"以下是联网检索到的参考片段：\n{context}\n\n"
        f"请依据以上片段回答学生的问题，并在关键结论后标注（来源[编号]）。"
    )

    answer_text = generate(prompt, system=WEB_SYSTEM_PROMPT)
    if not answer_text:
        return {"ok": False, "answer": "", "source": "", "matched": "web"}

    sources = "、".join(r.get("title", "")[:24] for r in web_results[:3])
    return {
        "ok": True,
        "answer": answer_text,
        "source": "互联网检索（必应/百度）",
        "matched": "web_llm",
    }


# ---------- 5. 知识库+联网 融合回答（第四轮新增） ----------
FUSED_SYSTEM_PROMPT = (
    "你是「云智」，一位部署在高职云计算实训课堂的本地化 AI 助教。\n"
    "本次回答综合两类参考材料：【A. 私有知识库片段】（本校/教材权威内容）和 "
    "【B. 网络检索片段】（互联网最新资料）。\n"
    "请严格遵循以下规则：\n"
    "1. **优先依据 A 知识库**：知识库是本校教材/指导书内容，是权威参考。\n"
    "2. **A 不足时补充 B 联网**：当知识库内容不完整、命令过时、或缺少最新资料时，"
    "用联网片段补充，并以（联网[编号]）标注来源。\n"
    "3. **冲突处理**：知识库与联网内容冲突时，**优先采用知识库**，并在末尾说明 "
    "「如联网结果与教材有出入，以教材为准」。\n"
    "4. **结论先行、分点清晰**，面向高职学生用通俗语言；命令用代码块，步骤用有序列表。\n"
    "5. 不要输出任何无关或敏感内容。"
)


def answer_fused(question, kb_chunks=None, web_results=None):
    """知识库 + 联网 融合回答

    参数：
        question     学生原始问题
        kb_chunks    list[{content, source}, ...]  本地知识库检索片段（来自 retrieve）
        web_results  list[{title,url,snippet}, ...] 联网搜索结果
    返回 {"ok": bool, "answer": str, "source": str, "matched": str}
        ok=False 表示 Ollama 不可用，上层可降级为罗列模式
    """
    kb_chunks = kb_chunks or []
    web_results = web_results or []

    # 构建【A. 私有知识库片段】
    kb_context = ""
    for i, c in enumerate(kb_chunks, 1):
        src = c.get("source", "知识库")
        kb_context += f"【A{i}｜来源：{src}】\n{c.get('content','')[:600]}\n\n"

    # 构建【B. 网络检索片段】
    web_context = ""
    for i, r in enumerate(web_results, 1):
        web_context += (f"【B{i}｜来源：{r.get('title','')}｜URL：{r.get('url','')}】\n"
                        f"{r.get('snippet','')[:400]}\n\n")

    if not kb_context and not web_context:
        return {"ok": False, "answer": "", "source": "", "matched": "fused"}

    prompt = (
        f"学生问题：{question}\n\n"
        f"============ A. 私有知识库片段 ============\n"
        f"{kb_context or '（本次检索未命中本地知识库）'}\n"
        f"============ B. 网络检索片段 ============\n"
        f"{web_context or '（本次未联网）'}\n\n"
        f"请综合以上 A、B 两类参考材料，回答学生问题。"
        f"知识库引用标（A1/A2...），联网引用标（联网1/2...），"
        f"最后追加一句「如联网结果与教材有出入，以教材为准」。"
    )

    answer_text = generate(prompt, system=FUSED_SYSTEM_PROMPT)
    if not answer_text:
        # Ollama 不可用：让上层降级为「知识库原文 + 联网结果罗列」
        # 错误信息已在 generate() 中记录到 _last_generate_error
        return {"ok": False, "answer": "", "source": "", "matched": "fused",
                "reason": "model_down"}

    sources = []
    for c in kb_chunks[:2]:
        if c.get("source"):
            sources.append(c["source"])
    for r in web_results[:2]:
        if r.get("title"):
            sources.append("联网:" + r["title"][:20])
    src_str = "、".join(sources) if sources else "知识库+联网"

    return {
        "ok": True,
        "answer": answer_text,
        "source": src_str,
        "matched": "fused",
    }


# ---------- 本地测试 ----------
if __name__ == "__main__":
    print("Ollama 地址:", OLLAMA_HOST)
    print("默认模型:", OLLAMA_MODEL)
    ok, info = check_available()
    print("服务在线:", ok, info)

    if ok:
        print("已安装模型:", info.get("models"))
        print("目标模型已安装:", model_installed())

        # 测试 RAG
        q = "VPC 对等连接怎么配置？"
        print("\n问题:", q)
        res = retrieve(q, top_k=3)
        for r in res:
            print(f"  - [{r['type']}] {r['title']} | {r['source']}")
        print("\nRAG 回答测试：")
        ans = rag_answer(q)
        print("ok:", ans["ok"], "| matched:", ans["matched"])
        print(ans["answer"][:300])
