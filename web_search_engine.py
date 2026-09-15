# -*- coding: utf-8 -*-
"""
云智实训助手 · 互联网搜索兜底引擎
==================================

职责（对齐项目规范 v2 · 竞赛版）：
    当「知识库关键词匹配」和「知识库 RAG 检索」都未命中时，
    从互联网检索公开资料作为兜底信息源，保证学生的问题始终有出口。

检索策略：
    引擎按顺序回退（前一个失败/无结果自动切下一个）：
        1. 必应中国  cn.bing.com          —— 国内机房可达性最好
        2. 百度      www.baidu.com        —— 备用国内源
        3. DuckDuckGo Lite                —— 国际网络环境备用

安全与合规红线（不因联网而放松）：
    - 上层 qa_engine 已做「提示词注入检测」与「实训范围白名单」，
      只有通过校验的实训类问题才会进入本模块；
    - 出站数据仅包含「技术查询关键词」，不含学生姓名、学号、IP 等身份信息；
    - 只提取搜索结果的标题 / 链接 / 摘要纯文本，不加载任何脚本、图片或 Cookie 池；
    - 回答必须标注来源 URL，可溯源、可核对；
    - 开关：环境变量 ENABLE_WEB_SEARCH=0 可一键关闭联网（恢复纯本地模式）。

配置（环境变量，均有默认值）：
    ENABLE_WEB_SEARCH   是否启用联网兜底        默认 1（启用）
    WEB_SEARCH_TIMEOUT  单引擎请求超时（秒）     默认 8
    WEB_SEARCH_TOP_K    最多取用的结果条数       默认 5
"""

import os
import re
import html
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

# ---------- 配置 ----------
ENABLE_WEB_SEARCH = os.environ.get("ENABLE_WEB_SEARCH", "1") == "1"
SEARCH_TIMEOUT = int(os.environ.get("WEB_SEARCH_TIMEOUT", "8"))
TOP_K = int(os.environ.get("WEB_SEARCH_TOP_K", "5"))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
    "Referer": "https://cn.bing.com/",
}


# ---------- 底层 HTTP ----------
def _http_get(url, timeout=None):
    """带浏览器 UA 的 GET，返回解码后的 HTML 文本"""
    timeout = timeout or SEARCH_TIMEOUT
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _clean(text):
    """去标签残留、压缩空白、反转义 HTML 实体"""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _dedup(results):
    """按 URL 去重，保留先出现的"""
    seen, out = set(), []
    for r in results:
        u = r.get("url", "")
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(r)
    return out


# 相关性过滤时的中文停用 2-gram（疑问虚词 + 高频泛义词）
_STOP_GRAMS = {"什么", "怎么", "如何", "为何", "怎样", "请问", "哪些",
               "为什", "何做", "做什", "一下", "作用", "用途", "意思",
               "详解", "解释", "方法", "使用", "多多", "多少"}
_STOP_CHARS = "的了吗呢吧啊哦与和及或对关于请"


def _query_features(query):
    """从查询词提取用于相关性判断的特征：英文技术词 + 中文 2-gram"""
    q = query.lower()
    eng_terms = [t for t in re.findall(r"[a-z0-9][a-z0-9\.\-_]{1,}", q) if t not in ("http", "https", "com", "cn", "www")]
    cn = re.sub(r"[^\u4e00-\u9fff]", " ", query)
    grams = set()
    for seg in cn.split():
        seg = "".join(ch for ch in seg if ch not in _STOP_CHARS)
        if len(seg) >= 2:
            grams |= {seg[i:i + 2] for i in range(len(seg) - 1)}
    grams -= _STOP_GRAMS
    return eng_terms, grams


def _hit_counts(query, result):
    """统计结果标题/正文中命中的查询特征数量（先剔除查询词回显，防假命中）"""
    title = result.get("title", "").lower()
    text = title + " " + result.get("snippet", "").lower()
    # 降级页/广告页常把查询原句回显在摘要里，先剔除再判相关性
    text = text.replace(query.lower(), "")
    eng_terms, grams = _query_features(query)
    eng_hits = sum(1 for t in eng_terms if t in text)
    title_hits = sum(1 for g in grams if g in title.replace(query.lower(), ""))
    any_hits = sum(1 for g in grams if g in text)
    return eng_terms, eng_hits, title_hits, any_hits


def _is_relevant(query, result):
    """
    严格相关性校验：
      有英文技术词 → 必须命中，且中文 gram 命中（标题≥1 或 全文≥2）
      纯中文查询   → 标题命中≥1 或 全文命中≥3
      查询本身无有效特征（全停用词）→ 无法判断，放行
    """
    eng_terms, eng_hits, title_hits, any_hits = _hit_counts(query, result)
    if eng_terms:
        return eng_hits >= 1 and (title_hits >= 1 or any_hits >= 2)
    _, grams = _query_features(query)
    if not grams:
        return True  # 查询全是停用词，无法判断相关性 → 放行
    return title_hits >= 1 or any_hits >= 3


def _quality_score(query, results):
    """引擎结果质量分：严格相关条目占比"""
    if not results:
        return 0.0
    relevant = sum(1 for r in results if _is_relevant(query, r))
    return relevant / len(results)


# ---------- 引擎 1：必应中国 ----------
def _search_bing(query):
    """cn.bing.com 结果解析：li.b_algo 内 h2>a 为标题链接，p 为摘要"""
    url = "https://cn.bing.com/search?" + urllib.parse.urlencode(
        {"q": query, "count": 10, "setlang": "zh-hans"})
    soup = BeautifulSoup(_http_get(url), "html.parser")
    results = []
    for li in soup.select("li.b_algo"):
        a = li.select_one("h2 a")
        if not a or not a.get("href"):
            continue
        snippet_node = li.select_one(".b_caption p") or li.select_one("p")
        results.append({
            "title": _clean(a.get_text()),
            "url": a["href"],
            "snippet": _clean(snippet_node.get_text()) if snippet_node else "",
        })
    return results


# ---------- 引擎 2：百度 ----------
def _search_baidu(query):
    """百度结果解析：div.c-container 内 h3>a 为标题链接，摘要取容器文本"""
    url = "https://www.baidu.com/s?" + urllib.parse.urlencode({"wd": query, "rn": 10})
    soup = BeautifulSoup(_http_get(url), "html.parser")
    results = []
    for box in soup.select("div.c-container, div.result"):
        a = box.select_one("h3 a")
        if not a or not a.get("href"):
            continue
        # 百度摘要 class 名经常变化，退化为取容器全文再去掉标题
        snippet = _clean(box.get_text())
        title = _clean(a.get_text())
        if title and snippet.startswith(title):
            snippet = snippet[len(title):].strip()
        results.append({"title": title, "url": a["href"], "snippet": snippet[:300]})
    return results


# ---------- 引擎 3：必应 RSS 接口（反爬宽松，稳定性最好）----------
def _search_bing_rss(query):
    """必应官方 RSS 输出：XML 解析，无验证码/降级页问题"""
    import xml.etree.ElementTree as ET
    url = "https://www.bing.com/search?" + urllib.parse.urlencode(
        {"q": query, "format": "rss", "count": 10, "mkt": "zh-CN"})
    root = ET.fromstring(_http_get(url))
    results = []
    for item in root.iter("item"):
        title = _clean(item.findtext("title", ""))
        link = (item.findtext("link", "") or "").strip()
        desc = _clean(item.findtext("description", ""))
        if title and link:
            results.append({"title": title, "url": link, "snippet": desc})
    return results


# ---------- 引擎 4：搜狗 ----------
def _search_sogou(query):
    """搜狗结果解析：div.vrwrap / div.rb 内 h3>a 为标题链接"""
    url = "https://www.sogou.com/web?" + urllib.parse.urlencode({"query": query})
    soup = BeautifulSoup(_http_get(url), "html.parser")
    results = []
    for box in soup.select("div.vrwrap, div.rb"):
        a = box.select_one("h3 a")
        if not a or not a.get("href"):
            continue
        href = a["href"]
        if href.startswith("/link"):
            href = "https://www.sogou.com" + href
        sn = box.select_one(".space-txt, .str-text-info, p.str_info, .str_info")
        results.append({
            "title": _clean(a.get_text()),
            "url": href,
            "snippet": _clean(sn.get_text()) if sn else "",
        })
    return results


# ---------- 引擎 5：DuckDuckGo Lite ----------
def _search_ddg(query):
    """DuckDuckGo Lite 结果解析（国际网络环境备用）"""
    url = "https://lite.duckduckgo.com/lite/?" + urllib.parse.urlencode({"q": query})
    soup = BeautifulSoup(_http_get(url), "html.parser")
    results = []
    for a in soup.select("a.result-link"):
        row = a.find_parent("tr")
        snippet = ""
        if row:
            nxt = row.find_next_sibling("tr")
            if nxt:
                snippet = _clean(nxt.get_text())
        results.append({
            "title": _clean(a.get_text()),
            "url": a.get("href", ""),
            "snippet": snippet,
        })
    return results


ENGINES = [
    ("必应RSS", _search_bing_rss),   # RSS 接口反爬最宽松，放首位
    ("百度", _search_baidu),
    ("必应", _search_bing),
    ("搜狗", _search_sogou),
    ("DuckDuckGo", _search_ddg),
]


# ---------- 对外主入口 ----------
def search(query, top_k=None):
    """
    联网搜索主入口（质量择优策略）
    流程：逐个引擎检索 → 严格过滤无关结果 → 质量分≥0.5 直接采用；
          全部试完后仍无合格引擎 → 返回质量分最高的结果（聊胜于无）
    返回：{"ok": bool, "engine": str, "results": [...], "error": str}
    """
    if not ENABLE_WEB_SEARCH:
        return {"ok": False, "engine": "", "results": [], "error": "联网搜索未启用（ENABLE_WEB_SEARCH=0）"}
    query = (query or "").strip()
    if not query:
        return {"ok": False, "engine": "", "results": [], "error": "查询词为空"}

    limit = top_k or TOP_K
    last_error = ""
    best = None  # (score, engine, results)

    for idx, (name, fn) in enumerate(ENGINES):
        try:
            if idx > 0:
                import time
                time.sleep(0.8)  # 引擎间延迟，降低反爬触发概率
            results = fn(query)
            results = [r for r in results if r.get("title") and r.get("url")]
            results = [r for r in results if _is_relevant(query, r)]
            results = _dedup(results)[:limit]
            if not results:
                last_error = f"{name} 无有效结果"
                continue
            score = _quality_score(query, results)
            if score >= 0.5:
                return {"ok": True, "engine": name, "results": results, "error": ""}
            if best is None or score > best[0]:
                best = (score, name, results)
        except Exception as e:
            last_error = f"{name} 失败: {e}"

    if best and best[2]:
        return {"ok": True, "engine": best[1], "results": best[2], "error": ""}
    return {"ok": False, "engine": "", "results": [], "error": last_error or "所有搜索引擎均不可达"}


def format_results_for_context(results):
    """把搜索结果拼成给大模型的上下文片段（带来源编号）"""
    parts = []
    for i, r in enumerate(results, 1):
        parts.append(
            f"【网络检索片段{i}｜来源：{r['title']}｜URL：{r['url']}】\n{r['snippet']}"
        )
    return "\n\n".join(parts)


def format_results_as_html(results):
    """Ollama 不可用时，直接把搜索结果渲染为可读 HTML（兜底的兜底）"""
    items = []
    for i, r in enumerate(results, 1):
        snippet = r.get("snippet", "")
        url = r.get("url", "#")
        items.append(
            f"{i}. <strong>{html.escape(r['title'])}</strong><br>"
            f"&nbsp;&nbsp;&nbsp;{html.escape(snippet[:200])}<br>"
            f"&nbsp;&nbsp;&nbsp;<a href='{html.escape(url, quote=True)}' target='_blank' "
            f"rel='noopener noreferrer' style='color:#2563eb;word-break:break-all;'>"
            f"来源链接</a>"
        )
    return "<br><br>".join(items)


# ---------- 查询词清洗 ----------
# 学生说"联网搜一下 nginx 反向代理"时，去掉意图词，只留技术关键词
INTENT_NOISE = re.compile(
    r"(请|帮我|麻烦)?(联网|上网|在线)?(搜索|搜一下|搜一搜|搜查|查一下|查查|查询|查一查|检索)(一下|下|看看)?(资料|信息)?(关于|有关)?",
)


def clean_query(question):
    """把学生的原始提问转成适合搜索引擎的查询词（去意图词、去标点）"""
    q = INTENT_NOISE.sub(" ", question)
    q = re.sub(r"[?？!！。，,、：:;；~～\"'\"]+", " ", q)   # 问号等标点会干扰引擎
    q = re.sub(r"^(一下|下|看看)[\s,,，、]*", "", q.strip())
    q = re.sub(r"[\s,,，、]+$", "", q).strip()
    q = re.sub(r"\s{2,}", " ", q)
    return q or question.strip()


# ---------- 本地测试 ----------
if __name__ == "__main__":
    print("联网搜索开关:", "启用" if ENABLE_WEB_SEARCH else "关闭")
    for q in ["nginx 反向代理 配置方法", "Docker Compose volumes 用法"]:
        print("=" * 50)
        print("查询:", q)
        r = search(q)
        print("引擎:", r["engine"], "| ok:", r["ok"], "| error:", r["error"])
        for item in r["results"][:3]:
            print(f"  - {item['title']}\n    {item['url']}\n    {item['snippet'][:80]}")
