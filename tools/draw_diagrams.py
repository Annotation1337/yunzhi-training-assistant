# -*- coding: utf-8 -*-
"""
用 Pillow 绘制几张云计算示意图，作为知识库预设图片。
"""
import os
from PIL import Image, ImageDraw, ImageFont

# 中文字体
FONT_PATHS = [
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
]

def get_font(size=20):
    for p in FONT_PATHS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images')  # 项目根 images/
os.makedirs(OUT_DIR, exist_ok=True)

# 配色
BG = (255, 255, 255)
INK = (40, 50, 60)
BLUE = (52, 120, 198)
BLUE_LIGHT = (200, 220, 245)
GREEN = (60, 170, 90)
GREEN_LIGHT = (215, 240, 220)
ORANGE = (230, 130, 50)
ORANGE_LIGHT = (250, 220, 200)
PURPLE = (130, 80, 180)
PURPLE_LIGHT = (225, 210, 240)
GRAY = (180, 185, 190)
GRAY_LIGHT = (235, 235, 240)
RED = (200, 60, 60)

def text(draw, xy, s, font, fill=INK):
    draw.text(xy, s, font=font, fill=fill)

def box(draw, xy, fill, outline=INK, w=2, r=6):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=w)


# ============================================
# 1. VPC 拓扑图 (VPC 包含子网、ECS、RDS)
# ============================================
def vpc_topology():
    W, H = 900, 560
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = get_font(26)
    f_h = get_font(18)
    f_n = get_font(16)
    f_s = get_font(14)

    # 标题
    text(d, (30, 16), 'VPC 虚拟私有云 拓扑示意', f_title, BLUE)
    text(d, (30, 50), 'CIDR: 10.0.0.0/16', f_s, INK)

    # VPC 边界
    box(d, (30, 80, W-30, H-30), GRAY_LIGHT, BLUE, w=2, r=10)
    text(d, (40, 90), 'VPC 10.0.0.0/16', f_n, BLUE)

    # 子网 A
    box(d, (70, 140, 430, 420), GREEN_LIGHT, GREEN, w=2, r=8)
    text(d, (90, 152), '子网 A  10.0.1.0/24  (可用区 A)', f_n, GREEN)

    # 子网 B
    box(d, (470, 140, 870, 420), ORANGE_LIGHT, ORANGE, w=2, r=8)
    text(d, (490, 152), '子网 B  10.0.2.0/24  (可用区 B)', f_n, ORANGE)

    # ECS 实例（子网 A）
    box(d, (110, 200, 230, 290), BG, BLUE, w=2, r=6)
    text(d, (140, 215), 'ECS-1', f_h, BLUE)
    text(d, (115, 245), '10.0.1.10', f_s, INK)
    text(d, (130, 265), 'Web 服务', f_s, INK)

    box(d, (250, 200, 370, 290), BG, BLUE, w=2, r=6)
    text(d, (280, 215), 'ECS-2', f_h, BLUE)
    text(d, (255, 245), '10.0.1.11', f_s, INK)
    text(d, (270, 265), 'Web 服务', f_s, INK)

    # RDS 数据库
    box(d, (180, 320, 320, 400), BG, PURPLE, w=2, r=6)
    text(d, (220, 332), 'RDS', f_h, PURPLE)
    text(d, (195, 360), '10.0.1.50', f_s, INK)
    text(d, (200, 378), 'MySQL 主库', f_s, INK)

    # ECS（子网 B）
    box(d, (510, 200, 630, 290), BG, BLUE, w=2, r=6)
    text(d, (540, 215), 'ECS-3', f_h, BLUE)
    text(d, (515, 245), '10.0.2.10', f_s, INK)
    text(d, (530, 265), 'App 服务', f_s, INK)

    box(d, (650, 200, 770, 290), BG, BLUE, w=2, r=6)
    text(d, (680, 215), 'ECS-4', f_h, BLUE)
    text(d, (655, 245), '10.0.2.11', f_s, INK)
    text(d, (670, 265), 'App 服务', f_s, INK)

    # NAT 网关
    box(d, (510, 320, 770, 400), BG, ORANGE, w=2, r=6)
    text(d, (580, 332), 'NAT 网关', f_h, ORANGE)
    text(d, (575, 360), '共享公网出口', f_s, INK)
    text(d, (590, 378), 'EIP: 1.2.3.4', f_s, INK)

    # 路由器
    box(d, (W//2 - 60, 440, W//2 + 60, 490), GRAY, GRAY, w=2, r=6)
    text(d, (W//2 - 40, 452), 'VPC Router', f_n, BG)

    # 连接线
    for (x1, y1, x2, y2) in [
        (170, 290, 170, 320),  # ECS-1 -> RDS
        (310, 290, 310, 320),  # ECS-2 -> RDS
        (570, 290, 570, 320),  # ECS-3 -> NAT
        (710, 290, 710, 320),  # ECS-4 -> NAT
        (250, 320, 250, 400),  # RDS
        (250, 400, W//2, 440),  # RDS -> Router
        (640, 400, W//2, 440),  # NAT -> Router
    ]:
        d.line([(x1, y1), (x2, y2)], fill=GRAY, width=2)

    # 公网标识
    text(d, (30, 510), '→ 子网必须在 VPC CIDR 范围内,  不同可用区提供容灾', f_s, INK)

    img.save(os.path.join(OUT_DIR, 'vpc_topology.png'))
    print('  ✓ vpc_topology.png')


# ============================================
# 2. Docker vs 虚拟机 对比图
# ============================================
def docker_vs_vm():
    W, H = 900, 580
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = get_font(26)
    f_h = get_font(20)
    f_n = get_font(16)
    f_s = get_font(13)

    text(d, (260, 16), 'Docker 容器 vs 虚拟机', f_title, BLUE)

    # 左侧: 虚拟机
    box(d, (60, 70, 420, 540), GRAY_LIGHT, GRAY, w=2, r=10)
    text(d, (200, 85), '虚拟机 (VM)', f_h, INK)
    base_y = 130
    # 硬件
    box(d, (90, base_y, 390, base_y+50), BLUE, BLUE, w=1, r=4)
    text(d, (190, base_y+15), '物理硬件', f_s, BG)
    # Host OS
    box(d, (90, base_y+60, 390, base_y+100), GREEN, GREEN, w=1, r=4)
    text(d, (190, base_y+72), 'Host 操作系统', f_s, BG)
    # Hypervisor
    box(d, (90, base_y+110, 390, base_y+140), PURPLE, PURPLE, w=1, r=4)
    text(d, (170, base_y+118), 'Hypervisor (VMware/KVM)', f_s, BG)
    # Guest OS 1
    box(d, (100, base_y+155, 240, base_y+215), ORANGE_LIGHT, ORANGE, w=1, r=4)
    text(d, (130, base_y+165), 'Guest OS 1', f_s, INK)
    box(d, (110, base_y+180, 230, base_y+205), BG, ORANGE, w=1, r=4)
    text(d, (140, base_y+186), 'App A', f_s, ORANGE)
    # Guest OS 2
    box(d, (250, base_y+155, 390, base_y+215), ORANGE_LIGHT, ORANGE, w=1, r=4)
    text(d, (280, base_y+165), 'Guest OS 2', f_s, INK)
    box(d, (260, base_y+180, 380, base_y+205), BG, ORANGE, w=1, r=4)
    text(d, (290, base_y+186), 'App B', f_s, ORANGE)
    # 注解
    text(d, (90, base_y+230), '· 启动: 分钟级', f_s, INK)
    text(d, (90, base_y+250), '· 体积: GB 级', f_s, INK)
    text(d, (90, base_y+270), '· 资源损耗: 5-15%', f_s, INK)
    text(d, (90, base_y+290), '· 隔离: 完全隔离', f_s, INK)
    text(d, (90, base_y+320), '每台 VM 都有独立 OS', f_h, BLUE)

    # 右侧: 容器
    box(d, (480, 70, 840, 540), GRAY_LIGHT, BLUE, w=2, r=10)
    text(d, (620, 85), 'Docker 容器', f_h, INK)
    base_y = 130
    # 硬件
    box(d, (510, base_y, 810, base_y+50), BLUE, BLUE, w=1, r=4)
    text(d, (610, base_y+15), '物理硬件', f_s, BG)
    # Host OS
    box(d, (510, base_y+60, 810, base_y+100), GREEN, GREEN, w=1, r=4)
    text(d, (610, base_y+72), 'Host 操作系统 (共享)', f_s, BG)
    # Docker Engine
    box(d, (510, base_y+110, 810, base_y+140), BLUE, BLUE, w=1, r=4)
    text(d, (590, base_y+118), 'Docker Engine (容器运行时)', f_s, BG)
    # Container 1
    box(d, (520, base_y+155, 660, base_y+215), GREEN_LIGHT, GREEN, w=1, r=4)
    text(d, (550, base_y+165), 'Container 1', f_s, INK)
    box(d, (530, base_y+180, 650, base_y+205), BG, GREEN, w=1, r=4)
    text(d, (560, base_y+186), 'App A', f_s, GREEN)
    # Container 2
    box(d, (670, base_y+155, 810, base_y+215), GREEN_LIGHT, GREEN, w=1, r=4)
    text(d, (700, base_y+165), 'Container 2', f_s, INK)
    box(d, (680, base_y+180, 800, base_y+205), BG, GREEN, w=1, r=4)
    text(d, (710, base_y+186), 'App B', f_s, GREEN)
    # 注解
    text(d, (510, base_y+230), '· 启动: 秒级', f_s, INK)
    text(d, (510, base_y+250), '· 体积: MB 级', f_s, INK)
    text(d, (510, base_y+270), '· 资源损耗: < 2%', f_s, INK)
    text(d, (510, base_y+290), '· 隔离: 进程级', f_s, INK)
    text(d, (510, base_y+320), '共享宿主机内核, 无 Guest OS', f_h, GREEN)

    img.save(os.path.join(OUT_DIR, 'docker_vs_vm.png'))
    print('  ✓ docker_vs_vm.png')


# ============================================
# 3. 负载均衡架构图
# ============================================
def slb_architecture():
    W, H = 900, 480
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = get_font(26)
    f_h = get_font(20)
    f_n = get_font(16)
    f_s = get_font(14)

    text(d, (270, 16), '负载均衡 (SLB) 架构示意', f_title, BLUE)

    # 客户端
    box(d, (60, 200, 200, 280), PURPLE_LIGHT, PURPLE, w=2, r=8)
    text(d, (110, 220), '客户端', f_h, PURPLE)
    text(d, (95, 248), '用户浏览器', f_s, INK)
    text(d, (110, 268), '/ App', f_s, INK)

    # 负载均衡器
    box(d, (320, 170, 580, 310), ORANGE_LIGHT, ORANGE, w=2, r=10)
    text(d, (400, 190), '负载均衡器', f_h, ORANGE)
    text(d, (430, 218), 'VIP', f_n, ORANGE)
    text(d, (360, 240), '· 健康检查', f_s, INK)
    text(d, (360, 258), '· 流量分发', f_s, INK)
    text(d, (360, 276), '· 故障剔除', f_s, INK)
    text(d, (370, 294), '4 层 TCP / 7 层 HTTP', f_s, INK)

    # 后端 4 台
    backends = [
        (660, 110, 800, 180, 'ECS-1', 'OK'),
        (660, 200, 800, 270, 'ECS-2', 'OK'),
        (660, 290, 800, 360, 'ECS-3', '故障'),
        (820, 110, 850, 180, '4', 'OK'),
    ]
    # 重画整齐
    for x, y, x2, y2, name, st in [
        (640, 110, 770, 180, 'ECS-1', 'OK'),
        (790, 110, 870, 180, 'ECS-2', 'OK'),
        (640, 220, 770, 290, 'ECS-3', '故障'),
        (790, 220, 870, 290, 'ECS-4', 'OK'),
    ]:
        color = GREEN_LIGHT if st == 'OK' else (255, 200, 200)
        outcolor = GREEN if st == 'OK' else RED
        box(d, (x, y, x2, y2), color, outcolor, w=2, r=6)
        text(d, (x+25, y+12), name, f_n, outcolor)
        text(d, (x+35, y+45), st, f_s, outcolor)

    # 注解
    text(d, (60, 340), '工作流程:', f_h, INK)
    text(d, (60, 365), '  ① 客户端访问 VIP（公网 IP）', f_s, INK)
    text(d, (60, 385), '  ② SLB 按策略转发到 ECS-1/2/4（ECS-3 健康检查失败，已剔除）', f_s, INK)
    text(d, (60, 405), '  ③ ECS 处理请求并返回', f_s, INK)
    text(d, (60, 425), '  → ECS-3 恢复后 SLB 自动加回', f_s, GREEN)

    # 连接线
    d.line([(200, 240), (320, 240)], fill=GRAY, width=2)
    # 客户端 -> SLB 中点
    for x in [705, 830, 705, 830]:
        y = 250
        d.line([(580, 240), (x, y - 70 if y == 250 else 110)], fill=GRAY, width=2)

    # 重画连接线：SLB 到 4 个 ECS
    for y in [145, 145, 255, 255]:
        d.line([(580, 240), (620, y)], fill=GRAY, width=2)
    d.line([(580, 240), (620, 145)], fill=GRAY, width=2)
    d.line([(580, 240), (620, 255)], fill=GRAY, width=2)
    d.line([(580, 240), (620, 145)], fill=GRAY, width=2)
    d.line([(580, 240), (620, 255)], fill=GRAY, width=2)

    img.save(os.path.join(OUT_DIR, 'slb_architecture.png'))
    print('  ✓ slb_architecture.png')


# ============================================
# 4. MySQL 主从架构图
# ============================================
def mysql_master_slave():
    W, H = 900, 480
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = get_font(26)
    f_h = get_font(20)
    f_n = get_font(16)
    f_s = get_font(14)

    text(d, (270, 16), 'MySQL 主从复制架构', f_title, BLUE)

    # App
    box(d, (60, 200, 220, 280), PURPLE_LIGHT, PURPLE, w=2, r=8)
    text(d, (110, 220), '应用', f_h, PURPLE)
    text(d, (95, 250), '读 / 写', f_s, INK)

    # Master
    box(d, (340, 180, 540, 300), ORANGE_LIGHT, ORANGE, w=2, r=10)
    text(d, (400, 200), 'Master 主库', f_h, ORANGE)
    text(d, (380, 230), '· 处理所有写', f_s, INK)
    text(d, (380, 250), '· binlog 记录变更', f_s, INK)
    text(d, (380, 270), '· MySQL 8.0', f_s, INK)

    # Slave 1
    box(d, (640, 80, 840, 180), GREEN_LIGHT, GREEN, w=2, r=8)
    text(d, (700, 100), 'Slave 从库 1', f_h, GREEN)
    text(d, (670, 130), '· 处理读请求', f_s, INK)
    text(d, (670, 150), '· 异步/半同步复制', f_s, INK)

    # Slave 2
    box(d, (640, 220, 840, 320), GREEN_LIGHT, GREEN, w=2, r=8)
    text(d, (700, 240), 'Slave 从库 2', f_h, GREEN)
    text(d, (670, 270), '· 处理读请求', f_s, INK)
    text(d, (670, 290), '· 灾备', f_s, INK)

    # 注解
    text(d, (60, 350), '工作流程:', f_h, INK)
    text(d, (60, 375), '  ① App 写 → Master', f_s, INK)
    text(d, (60, 395), '  ② Master 把变更写入 binlog', f_s, INK)
    text(d, (60, 415), '  ③ Slave 拉 binlog 并重放, 实现数据同步', f_s, INK)
    text(d, (60, 435), '  ④ App 读 → 任一 Slave (读写分离)', f_s, INK)

    # 箭头: App -> Master
    d.line([(220, 240), (340, 240)], fill=GRAY, width=2)
    d.polygon([(335, 235), (340, 240), (335, 245)], fill=GRAY)
    # Master -> Slaves (binlog 复制)
    d.line([(540, 220), (640, 130)], fill=ORANGE, width=2)
    d.line([(540, 260), (640, 270)], fill=ORANGE, width=2)
    # 读
    d.line([(220, 250), (640, 150)], fill=GRAY, width=2, )

    img.save(os.path.join(OUT_DIR, 'mysql_master_slave.png'))
    print('  ✓ mysql_master_slave.png')


# ============================================
# 5. 三层架构 (前端-后端-数据库)
# ============================================
def three_tier():
    W, H = 900, 540
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = get_font(26)
    f_h = get_font(22)
    f_n = get_font(16)
    f_s = get_font(14)

    text(d, (280, 16), 'Web 应用 三层架构', f_title, BLUE)

    # 用户
    text(d, (390, 80), '用户', f_h, PURPLE)
    box(d, (380, 110, 510, 170), PURPLE_LIGHT, PURPLE, w=2, r=8)

    # 第 1 层: 表示层
    box(d, (60, 220, 280, 330), BLUE_LIGHT, BLUE, w=2, r=10)
    text(d, (115, 235), '第 1 层: 表示层', f_h, BLUE)
    text(d, (90, 270), 'Nginx / CDN', f_s, INK)
    text(d, (90, 290), '静态资源 / 反向代理', f_s, INK)

    # 第 2 层: 业务层
    box(d, (320, 220, 580, 330), GREEN_LIGHT, GREEN, w=2, r=10)
    text(d, (370, 235), '第 2 层: 业务层', f_h, GREEN)
    text(d, (340, 270), '应用服务器集群', f_s, INK)
    text(d, (340, 290), 'Python / Java / Node.js', f_s, INK)

    # 第 3 层: 数据层
    box(d, (620, 220, 850, 330), ORANGE_LIGHT, ORANGE, w=2, r=10)
    text(d, (670, 235), '第 3 层: 数据层', f_h, ORANGE)
    text(d, (640, 270), 'MySQL / Redis', f_s, INK)
    text(d, (640, 290), '持久化 + 缓存', f_s, INK)

    # 注解
    text(d, (60, 380), '请求流向:', f_h, INK)
    text(d, (60, 410), '用户 → CDN/Nginx → 负载均衡 → 应用服务器 → 数据库/缓存 → 返回结果', f_s, INK)
    text(d, (60, 440), '特点:', f_h, INK)
    text(d, (60, 465), '  · 三层解耦, 可独立扩展', f_s, INK)
    text(d, (60, 485), '  · 表示层可集群化, 业务层可水平扩容, 数据层可读写分离', f_s, INK)
    text(d, (60, 505), '  · 这是绝大多数互联网应用的骨架', f_s, INK)

    # 箭头
    d.line([(440, 170), (170, 220)], fill=GRAY, width=2)
    d.polygon([(170, 215), (175, 222), (180, 220)], fill=GRAY)
    d.line([(280, 275), (320, 275)], fill=GRAY, width=2)
    d.line([(580, 275), (620, 275)], fill=GRAY, width=2)

    img.save(os.path.join(OUT_DIR, 'three_tier_architecture.png'))
    print('  ✓ three_tier_architecture.png')


# ============================================
# 6. K8s 集群架构
# ============================================
def k8s_architecture():
    W, H = 900, 580
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = get_font(26)
    f_h = get_font(20)
    f_n = get_font(16)
    f_s = font_s = get_font(13)

    text(d, (290, 16), 'Kubernetes 集群架构', f_title, BLUE)

    # Control Plane
    box(d, (40, 80, 860, 230), GRAY_LIGHT, PURPLE, w=2, r=10)
    text(d, (370, 95), 'Control Plane (控制平面)', f_h, PURPLE)

    # 4 个控制平面组件
    components = [
        (60, 130, 230, 210, 'API Server', 'RESTful 入口'),
        (250, 130, 420, 210, 'etcd', '键值数据库'),
        (440, 130, 610, 210, 'Scheduler', 'Pod 调度'),
        (630, 130, 800, 210, 'Controller Mgr', '状态控制'),
    ]
    for x, y, x2, y2, name, desc in components:
        box(d, (x, y, x2, y2), BG, PURPLE, w=2, r=6)
        text(d, (x+15, y+12), name, f_n, PURPLE)
        text(d, (x+15, y+45), desc, f_s, INK)

    # Worker Nodes
    box(d, (40, 280, 860, 530), GRAY_LIGHT, GREEN, w=2, r=10)
    text(d, (370, 295), 'Worker Nodes (工作节点)', f_h, GREEN)

    # 3 个 Node
    for i, name in enumerate(['Node 1', 'Node 2', 'Node 3']):
        x = 60 + i * 270
        box(d, (x, 330, x+240, 510), BG, GREEN, w=2, r=6)
        text(d, (x+15, 345), name, f_n, GREEN)
        text(d, (x+15, 370), 'kubelet + kube-proxy', f_s, INK)
        # 3 pods
        for j, pname in enumerate(['Pod A', 'Pod B', 'Pod C']):
            box(d, (x+15, 400+j*30, x+220, 425+j*30), GREEN_LIGHT, GREEN, w=1, r=4)
            text(d, (x+30, 405+j*30), pname, f_s, GREEN)

    text(d, (60, 545), '· Pod = 1+ 容器, 共享网络/存储', f_s, INK)
    text(d, (350, 545), '· 跨节点自动调度', f_s, INK)
    text(d, (600, 545), '· 故障自动迁移', f_s, INK)

    img.save(os.path.join(OUT_DIR, 'k8s_architecture.png'))
    print('  ✓ k8s_architecture.png')


if __name__ == '__main__':
    print('生成示意图...')
    vpc_topology()
    docker_vs_vm()
    slb_architecture()
    mysql_master_slave()
    three_tier()
    k8s_architecture()
    print('\n所有图片已生成到:', OUT_DIR)
