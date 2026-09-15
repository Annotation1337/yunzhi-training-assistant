# -*- coding: utf-8 -*-
"""
云智实训助手 · 知识库管理引擎
================================
职责：
    - 三个知识库(qa/task/trouble)的 读/写/增/删/改
    - 修改前自动备份到 knowledge/backup/<时间戳>/
    - 导出(zip)/ 导入(json 或 zip, 按 id 合并去重)
    - 元字段(version/total/_说明)保存时自动维护，不暴露给用户

设计原则：
    - 所有写操作先备份，失败回滚（写临时文件成功后原子替换）
    - id 自动生成且保持唯一
    - 字段校验宽松：缺字段给默认值，多余字段保留
"""

import json
import os
import re
import shutil
import time
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "knowledge")
BACKUP_DIR = os.path.join(KB_DIR, "backup")

# 三库配置：类型 → (文件名, 列表键, 必填字段, id 前缀)
KB_TYPES = {
    "qa": {
        "file": "qa_data.json",
        "list_key": "qa_list",
        "id_prefix": "qa",
        "label": "问答库",
        "fields": {
            "keywords": "关键词(逗号分隔,命中即召回)",
            "answer": "答案(支持 HTML/Markdown 风格标签)",
            "source": "来源(如《网络规划指导书》第3章)",
            "image": "配图路径(可空,如 images/vpc.png)",
        },
    },
    "task": {
        "file": "task_data.json",
        "list_key": "tasks",
        "id_prefix": "task",
        "label": "任务库",
        "fields": {
            "name": "任务名称",
            "keywords": "关键词(逗号分隔)",
            "goal": "任务目标",
            "env": "环境要求",
            "steps": "步骤列表 [{title, detail, expected}]",
            "acceptance": "验收标准",
            "questions": "思考题列表 [字符串]",
            "source": "来源",
        },
    },
    "trouble": {
        "file": "trouble_data.json",
        "list_key": "rules",
        "id_prefix": "trouble",
        "label": "排错库",
        "fields": {
            "name": "故障名称",
            "patterns": "报错特征(每行一个)",
            "causes": "可能原因(每行一个)",
            "commands": "排查命令(每行一个)",
            "solution": "解决方案",
            "principle": "原理说明",
            "source": "来源",
        },
    },
}


# ---------- 工具 ----------
def _load_kb(kb_type):
    """读整个 json 文件,返回 dict;文件损坏时返回 None"""
    cfg = KB_TYPES[kb_type]
    path = os.path.join(KB_DIR, cfg["file"])
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _backup_all(reason="manual"):
    """把三个 json 备份到 knowledge/backup/<时间戳>-<reason>/"""
    ts = time.strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"{ts}-{reason}")
    os.makedirs(dest, exist_ok=True)
    copied = []
    for cfg in KB_TYPES.values():
        src = os.path.join(KB_DIR, cfg["file"])
        if os.path.exists(src):
            shutil.copy2(src, dest)
            copied.append(cfg["file"])
    return {"dir": os.path.relpath(dest, KB_DIR), "files": copied}


def _atomic_write(path, data):
    """原子写:先写 .tmp 再替换,避免写一半断电损坏"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _next_id(items, prefix):
    """生成下一个唯一 id: qa_048 形式"""
    max_n = 0
    for it in items:
        m = re.match(rf"^{prefix}[_-]?(\d+)$", str(it.get("id", "")))
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"{prefix}_{max_n + 1:03d}"


def _recount_meta(data, kb_type):
    """保存前自动维护元字段(total 等)"""
    cfg = KB_TYPES[kb_type]
    lst = data.get(cfg["list_key"], [])
    data["total"] = len(lst)
    return data


# ---------- 查 ----------
def list_items(kb_type, keyword=""):
    """列出某库全部条目(带摘要),支持关键词过滤"""
    cfg = KB_TYPES.get(kb_type)
    if not cfg:
        return {"ok": False, "error": f"未知库类型 {kb_type}"}
    data = _load_kb(kb_type)
    if data is None:
        return {"ok": False, "error": f"{cfg['file']} 读取失败或不存在"}
    items = data.get(cfg["list_key"], [])
    kw = (keyword or "").strip().lower()

    out = []
    for it in items:
        # 摘要字段按库类型取
        if kb_type == "qa":
            title = "、".join((it.get("keywords") or [])[:4]) or "(无关键词)"
            summary = re.sub(r"<[^>]+>", "", str(it.get("answer", "")))[:60]
        elif kb_type == "task":
            title = it.get("name", "(未命名)")
            summary = str(it.get("goal", ""))[:60]
        else:
            title = it.get("name", "(未命名)")
            summary = str(it.get("solution", ""))[:60]
        if kw:
            blob = json.dumps(it, ensure_ascii=False).lower()
            if kw not in blob:
                continue
        out.append({"id": it.get("id", ""), "title": title, "summary": summary,
                    "source": it.get("source", "")})
    return {"ok": True, "kb_type": kb_type, "label": cfg["label"],
            "count": len(out), "total": len(items), "items": out}


def get_item(kb_type, item_id):
    """取单条完整内容"""
    cfg = KB_TYPES.get(kb_type)
    if not cfg:
        return {"ok": False, "error": f"未知库类型 {kb_type}"}
    data = _load_kb(kb_type)
    if data is None:
        return {"ok": False, "error": "知识库文件读取失败"}
    for it in data.get(cfg["list_key"], []):
        if str(it.get("id", "")) == str(item_id):
            return {"ok": True, "item": it}
    return {"ok": False, "error": f"未找到 id={item_id}"}


# ---------- 增 / 改 ----------
def save_item(kb_type, item, is_new=None):
    """新增或更新一条。
    item 里含 id → 更新;不含 id 或 id 为空/is_new=True → 新增(自动生成 id)
    写之前自动备份。"""
    cfg = KB_TYPES.get(kb_type)
    if not cfg:
        return {"ok": False, "error": f"未知库类型 {kb_type}"}
    data = _load_kb(kb_type)
    if data is None:
        return {"ok": False, "error": f"{cfg['file']} 读取失败,无法保存"}

    items = data.setdefault(cfg["list_key"], [])
    item = dict(item or {})
    item_id = str(item.get("id", "")).strip()

    # 自动判断:无 id → 新增
    if is_new is None:
        is_new = not item_id

    if is_new:
        item["id"] = _next_id(items, cfg["id_prefix"])
        items.append(item)
        action = "新增"
    else:
        # 更新:找同 id 条目替换
        for i, it in enumerate(items):
            if str(it.get("id", "")) == item_id:
                item["id"] = item_id
                items[i] = item
                break
        else:
            return {"ok": False, "error": f"未找到 id={item_id},如要新增请清空 id"}
        action = "更新"

    # 备份 + 原子写
    bak = _backup_all(reason=f"before-{action}-{kb_type}")
    _recount_meta(data, kb_type)
    _atomic_write(os.path.join(KB_DIR, cfg["file"]), data)
    return {"ok": True, "action": action, "id": item["id"], "backup": bak["dir"]}


# ---------- 删 ----------
def delete_item(kb_type, item_id):
    """删除一条(先备份)。"""
    cfg = KB_TYPES.get(kb_type)
    if not cfg:
        return {"ok": False, "error": f"未知库类型 {kb_type}"}
    data = _load_kb(kb_type)
    if data is None:
        return {"ok": False, "error": "知识库文件读取失败"}

    items = data.get(cfg["list_key"], [])
    remain = [it for it in items if str(it.get("id", "")) != str(item_id)]
    if len(remain) == len(items):
        return {"ok": False, "error": f"未找到 id={item_id}"}

    bak = _backup_all(reason=f"before-delete-{kb_type}")
    data[cfg["list_key"]] = remain
    _recount_meta(data, kb_type)
    _atomic_write(os.path.join(KB_DIR, cfg["file"]), data)
    return {"ok": True, "deleted": item_id, "backup": bak["dir"],
            "remain": len(remain)}


# ---------- 导出 / 导入 ----------
def export_all():
    """导出三个 json 为 zip(含 backup 目录说明),返回 zip 路径"""
    ts = time.strftime("%Y%m%d-%H%M%S")
    out = os.path.join(BACKUP_DIR, f"export-{ts}.zip")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for cfg in KB_TYPES.values():
            src = os.path.join(KB_DIR, cfg["file"])
            if os.path.exists(src):
                z.write(src, cfg["file"])
        # markdown 教材一并导出
        for d in sorted(os.listdir(KB_DIR)):
            dp = os.path.join(KB_DIR, d)
            if os.path.isdir(dp) and d != "backup":
                for f in os.listdir(dp):
                    if f.endswith(".md"):
                        z.write(os.path.join(dp, f), os.path.join(d, f))
    return {"ok": True, "zip": out, "name": os.path.basename(out)}


def import_data(file_stream, filename, merge=True):
    """导入 json 或 zip。
    merge=True:按 id 合并(同 id 覆盖,新 id 追加)
    merge=False:整库覆盖(危险,导入前也会备份)
    返回每库的统计。"""
    bak = _backup_all(reason="before-import")
    stats = {}
    supported = {cfg["file"]: t for t, cfg in KB_TYPES.items()}

    def _merge_one(kb_type, incoming_data):
        cfg = KB_TYPES[kb_type]
        local = _load_kb(kb_type)
        if local is None:
            return f"本地 {cfg['file']} 读取失败,跳过"
        items = local.setdefault(cfg["list_key"], [])
        if not merge:
            items = []
        idx = {str(it.get("id", "")): i for i, it in enumerate(items)}
        add = upd = 0
        for nit in incoming_data.get(cfg["list_key"], []):
            nid = str(nit.get("id", "")).strip()
            if nid and nid in idx:
                items[idx[nid]] = nit
                upd += 1
            else:
                if not nid:
                    nid = _next_id(items, cfg["id_prefix"])
                    nit["id"] = nid
                items.append(nit)
                idx[nid] = len(items) - 1
                add += 1
        local[cfg["list_key"]] = items
        _recount_meta(local, kb_type)
        _atomic_write(os.path.join(KB_DIR, cfg["file"]), local)
        return f"新增 {add} 条,覆盖 {upd} 条"

    try:
        name = (filename or "").lower()
        if name.endswith(".zip"):
            with zipfile.ZipFile(file_stream) as z:
                for n in z.namelist():
                    base = os.path.basename(n)
                    if base in supported:
                        data = json.loads(z.read(n).decode("utf-8"))
                        kb_type = supported[base]
                        stats[kb_type] = _merge_one(kb_type, data)
        elif name.endswith(".json"):
            data = json.load(file_stream)
            # 自动识别是哪种库(看顶层键)
            matched = False
            for t, cfg in KB_TYPES.items():
                if cfg["list_key"] in data:
                    stats[t] = _merge_one(t, data)
                    matched = True
            if not matched:
                return {"ok": False, "error": "JSON 里未找到 qa_list/tasks/rules 任何一个键"}
        else:
            return {"ok": False, "error": "只支持 .json 或 .zip 文件"}
        return {"ok": True, "stats": stats, "backup": bak["dir"]}
    except json.JSONDecodeError:
        return {"ok": False, "error": "JSON 格式错误,请检查文件"}
    except zipfile.BadZipFile:
        return {"ok": False, "error": "zip 文件损坏"}
    except Exception as e:
        return {"ok": False, "error": f"导入失败: {type(e).__name__}: {e}"}


# ---------- Markdown 教材(只读) ----------
def list_docs():
    """列出 knowledge/ 下的 markdown 教材(只读查看)"""
    docs = []
    for d in sorted(os.listdir(KB_DIR)):
        dp = os.path.join(KB_DIR, d)
        if os.path.isdir(dp) and d != "backup":
            for f in sorted(os.listdir(dp)):
                if f.endswith(".md"):
                    docs.append({"dir": d, "file": f,
                                 "rel": os.path.join(d, f)})
    return {"ok": True, "docs": docs}


def get_doc(rel_path):
    """读一篇 markdown(限定在 knowledge 目录内,防路径穿越)"""
    full = os.path.normpath(os.path.join(KB_DIR, rel_path))
    if not full.startswith(os.path.abspath(KB_DIR)):
        return {"ok": False, "error": "非法路径"}
    if not os.path.exists(full):
        return {"ok": False, "error": "文件不存在"}
    with open(full, encoding="utf-8") as f:
        return {"ok": True, "content": f.read(), "rel": rel_path}


# ---------- 本地自测 ----------
if __name__ == "__main__":
    for t in KB_TYPES:
        r = list_items(t)
        print(f"{t}: {r.get('count')}/{r.get('total')}")
    r = list_items("qa", keyword="vpc")
    print("qa 搜 vpc:", r["count"], "条")
    print("docs:", len(list_docs()["docs"]), "篇")
