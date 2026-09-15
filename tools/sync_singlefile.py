# -*- coding: utf-8 -*-
"""
云智实训助手 · 单文件版数据同步脚本
====================================
将 knowledge/ 下的三个 JSON 数据同步到单文件版 云智实训助手.html 内联的三个 JS 常量：
    QA_DATA / TASK_DATA / TROUBLE_DATA

用法：
    python3 sync_singlefile.py
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根[脚本已移入 tools/]
HTML = os.path.join(BASE_DIR, "云智实训助手.html")


def load_json(name):
    p = os.path.join(BASE_DIR, "knowledge", name)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def find_js_block(content, const_name):
    """定位 const NAME = <value>; 的位置，返回 (start, end) 表示 value 的起止（含闭合符号，不含尾分号）"""
    m = re.search(r'const %s = ' % re.escape(const_name), content)
    if not m:
        return None
    val_start = m.end()  # value 开头（'[' 或 '{'）
    # 从开头字符开始括号配对
    start_char = content[val_start]
    if start_char not in "[{":
        return None
    open_c, close_c = (start_char, "]" if start_char == "[" else "}")
    depth = 0
    i = val_start
    in_str = False
    # 字符串转义处理
    while i < len(content):
        c = content[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == open_c:
                depth += 1
            elif c == close_c:
                depth -= 1
                if depth == 0:
                    # 结束位置为闭合符号之后（不含分号），分号由替换时统一补上
                    return (val_start, i + 1)
        i += 1
    return None


def sync():
    qa = load_json("qa_data.json")
    task = load_json("task_data.json")
    trouble = load_json("trouble_data.json")

    with open(HTML, encoding="utf-8") as f:
        content = f.read()

    updates = [
        ("QA_DATA", qa["qa_list"]),
        ("TASK_DATA", task["tasks"]),
        ("TROUBLE_DATA", trouble),
    ]

    for name, value in updates:
        block = find_js_block(content, name)
        if not block:
            print(f"[跳过] 未找到 {name} 定义位置")
            continue
        start, end = block
        # 吞掉紧随闭合符号后的分号（若有），由新值统一补一个
        if end < len(content) and content[end] == ";":
            end += 1
        new_json = json.dumps(value, ensure_ascii=False,
                              separators=(",", ":")) + ";"
        content = content[:start] + new_json + content[end:]
        print(f"[同步] {name}: 已更新 ({len(json.dumps(value, ensure_ascii=False))} 字符)")

    with open(HTML, "w", encoding="utf-8") as f:
        f.write(content)
    print("完成：单文件版数据已同步")


if __name__ == "__main__":
    sync()
