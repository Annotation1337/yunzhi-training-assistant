# -*- coding: utf-8 -*-
"""
云智实训助手 · 本地概念卡片生成器
=================================
当学生明确要求"画图 / 图片 / 示意图"时，若知识库无预置图，
则调用本模块在【本地】动态绘制一张概念示意图。

设计原则（对齐项目"数据绝对本地化"红线）：
    - 所有绘图均在本地完成，绝不外发任何数据。
    - 不调用任何外部 AI 生图服务；如需接入本地大模型绘图可在此扩展。

输出：
    images/card_<id>.png   生成的图片（相对站点的 url 根路径由调用方拼装）
    dict:
      {
        "url":  "images/card_xxx.png",
        "title": "主题标题",
        "path": "/absolute/path/to/card_xxx.png"
      }
"""

import os
import hashlib
import random
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根[脚本已移入 tools/]
IMG_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

# ---------- 中文字体 ----------
FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/arphic/ukai.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]


def get_font(size=20):
    """获取中文字体"""
    for p in FONT_PATHS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# 配色
INK = (45, 55, 72)
BLUE = (31, 111, 235)
GREEN = (46, 164, 79)
ORANGE = (243, 146, 42)
PURPLE = (124, 92, 206)
RED = (222, 86, 86)
GRAY = (150, 158, 172)
BG = (250, 251, 254)


def text(draw, xy, s, font, fill=INK, anchor="la"):
    draw.text(xy, s, font=font, fill=fill, anchor=anchor)


def box(draw, xy, fill, outline=INK, w=2, r=8):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=w)


def _wrap(s, font, max_w):
    """按像素宽度换行"""
    lines = []
    cur = ""
    for ch in s:
        if draw_width(cur + ch, font) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def draw_width(s, font):
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    return d.textlength(s, font=font)


def round_wrap(s, font, max_w):
    """计算换行后的宽度"""
    lines = _wrap(s, font, max_w)
    return lines


def gen_concept_card(card_id, title, points, hint=None):
    """
    生成一张概念卡片图
    card_id : 图片文件 id（用于小写文件名）
    title   : 卡片标题
    points  : 要点列表，每个要点为字符串，会分条渲染
    hint    : 底部提示（可为 None）
    返回 dict: {"url":..., "path":..., "title":...}
    """
    W = 760
    pad = 40
    title_font = get_font(34)
    sub_font = get_font(22)
    body_font = get_font(22)
    hint_font = get_font(20)

    # 先估算高度
    max_text_w = W - pad * 2 - 26  # 留出项目符号宽度
    lines = 0
    wrapped_points = []
    for pt in points:
        lp = round_wrap(pt, body_font, max_text_w)
        wrapped_points.append(lp)
        lines += len(lp)

    head_h = 96
    body_h = lines * 34 + 16
    tail_h = 60 if hint else 24
    H = head_h + body_h + tail_h

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 顶部色带 + 标题
    d.rectangle([0, 0, W, head_h - 6], fill=(240, 244, 252))
    d.rectangle([0, head_h - 6, W, head_h + 2], fill=BLUE)
    text(d, (W // 2, (head_h - 6) // 2 - 12), title, title_font, fill=INK, anchor="ma")

    # 要点
    y = head_h + 18
    for lines_ in wrapped_points:
        bullet_y = y + 22
        d.ellipse([pad, bullet_y - 7, pad + 12, bullet_y + 5], fill=BLUE)
        for ln in lines_:
            text(d, (pad + 26, y), ln, body_font, fill=INK)
            y += 34
        y += 6

    # 底部提示
    if hint:
        d.rectangle([0, H - tail_h + 6, W, H], fill=(240, 244, 252))
        text(d, (pad, H - tail_h + 24), hint, hint_font, fill=ORANGE)

    # 保存
    fname = f"card_{card_id}.png"
    path = os.path.join(IMG_DIR, fname)
    img.save(path)
    return {
        "url": f"images/{fname}",
        "path": path,
        "title": title,
    }


# ---------- 主题映射：根据关键词挑选卡片内容 ----------
CONCEPT_TOPICS = [
    {
        "keys": ["iaas", "paas", "saas", "服务模型"],
        "title": "云计算的三种服务模型",
        "points": [
            "IaaS 基础设施即服务：提供虚拟机、存储、网络，用户自己装系统与软件",
            "PaaS 平台即服务：提供运行环境（如数据库、中间件），用户只管应用",
            "SaaS 软件即服务：直接提供成品软件，用户开箱即用",
            "对比：越往上云厂商管得越多，用户管得越少",
        ],
        "hint": "理解：自助餐厅( IaaS ) vs 外卖半成品( PaaS ) vs 直接吃( SaaS )",
    },
    {
        "keys": ["公有云", "私有云", "混合云"],
        "title": "部署模型的三种云",
        "points": [
            "公有云：第三方厂商提供，按需付费，开箱即用",
            "私有云：企业自建自用，数据完全自主可控",
            "混合云：公有云 + 私有云 结合，兼顾弹性与安全",
        ],
        "hint": "高职实训通常使用私有云/混合云，数据不出校门",
    },
    {
        "keys": ["安全组", "防火墙", "访问控制", "iam", "权限"],
        "title": "安全组 / 访问控制要点",
        "points": [
            "安全组：云主机的虚拟防火墙，控制入/出方向流量",
            "默认只放行必要端口，如 22(SSH)、80/443(Web)",
            "规则：源IP + 端口 + 协议 白名单式放行",
            "IAM：用最小权限原则给不同角色授权",
        ],
        "hint": "最小权限：只给完成工作所需的最小访问权限",
    },
    {
        "keys": ["弹性", "伸缩", "扩容", "自动"],
        "title": "弹性伸缩（Auto Scaling）",
        "points": [
            "弹性 = 业务量大时自动增加实例，量小时自动减少",
            "基于监控指标（CPU / 请求数）触发伸缩策略",
            "冷启动：新实例就绪需时间，提前预热",
            "典型应用：电商大促、突发流量",
        ],
        "hint": "弹性是云计算的标志性优势之一",
    },
    {
        "keys": ["dns", "域名", "解析", "a记录"],
        "title": "DNS 域名解析流程",
        "points": [
            "A记录：域名 → IPv4 地址",
            "CNAME：域名 → 另一个域名（常用于CDN/负载均衡）",
            "解析流程：本地缓存 → 递归查询 → 权威服务器",
            "TTL：缓存时间，修改记录后需等待 TTL 生效",
        ],
        "hint": "修改DNS后不生效，多半是本地/TTL 缓存未刷新",
    },
    {
        "keys": ["redis", "缓存", "内存数据库"],
        "title": "Redis 缓存要点",
        "points": [
            "Redis：基于内存的高性能键值数据库",
            "常用于缓存热点数据、会话、排行榜",
            "优势：读快、支持多种数据结构、支持持久化",
            "注意：内存有限，需设置过期时间与淘汰策略",
        ],
        "hint": "缓存穿透、击穿、雪崩是常见考点",
    },
    {
        "keys": ["日志", "排错", "排查"],
        "title": "日志排错通用流程",
        "points": [
            "Step1 定位：查看应用日志 / 系统日志 / 服务状态",
            "    systemctl status 服务名  /  journalctl -u 服务名",
            "    tail -f /var/log/xxx.log",
            "Step2 复现：根据日志中的报错重现问题",
            "Step3 定位根因：结合错误码、堆栈、配置排查",
            "Step4 修复并验证，最后总结记录",
        ],
        "hint": "排错口诀：先看日志，再查配置，后看网络与权限",
    },
]

# 兜底卡片
DEFAULT_TOPIC = {
    "title": "云计算实训知识要点",
    "points": [
        "该主题暂无预置示意图，以下为概念卡片速览",
        "建议结合课堂指导书与现场教师进一步学习",
    ],
    "hint": "你可以把问题描述得更具体，或让老师补充讲解",
}


def get_card(question):
    """根据问题返回概念卡片，若无法匹配返回 None（由调用方决定是否用兜底）"""
    q = question.lower()
    for topic in CONCEPT_TOPICS:
        for k in topic["keys"]:
            if k.lower() in q:
                card_id = hashlib.md5(topic["title"].encode()).hexdigest()[:8]
                return gen_concept_card(card_id, topic["title"], topic["points"], topic.get("hint"))
    return None


def get_default_card():
    return gen_concept_card(
        hashlib.md5(DEFAULT_TOPIC["title"].encode()).hexdigest()[:8],
        DEFAULT_TOPIC["title"],
        DEFAULT_TOPIC["points"],
        DEFAULT_TOPIC.get("hint"),
    )


if __name__ == "__main__":
    r = get_card("什么是公有云私有云")
    print(r)
    r2 = get_default_card()
    print(r2)
