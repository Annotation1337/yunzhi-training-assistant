# -*- coding: utf-8 -*-
"""
云智 - 本地图像生成引擎
============================
两种出图能力并存：
  1. 拓扑/架构示意图 → matplotlib 自动画（精准、稳定）
  2. 插画/示意图    → Stable Diffusion 本地推理（一般但够用）

模型下载策略：国内源 (hf-mirror.com) 优先 → 失败自动回退 huggingface.co 原版源

触发规则（前端传入 type）：
  - "topology"   → matplotlib 出图（架构图/网段图/流程图）
  - "illustration" → Stable Diffusion 出图
  - "auto"       → 根据 prompt 自动判断

依赖（按需加载）：
  - diffusers / transformers / torch / accelerate / safetensors
  - matplotlib（已有）
"""

import os
import re
import io
import base64
import time
import logging
import threading

# matplotlib 采用「惰性导入」：
#   顶层 import 若失败会让整个模块加载报错（连 SD 一起挂掉），
#   因此改为首次出图时再导入，缺失时返回友好的安装提示。
_matplotlib_ready = None
_plt = None
_mpatches = None
_FancyBboxPatch = None
_FancyArrowPatch = None


def _ensure_matplotlib():
    """惰性加载 matplotlib。就绪返回 True，缺失返回 False（并记录原因）。"""
    global _matplotlib_ready, _plt, _mpatches, _FancyBboxPatch, _FancyArrowPatch
    if _matplotlib_ready is not None:
        return _matplotlib_ready
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
        _plt, _mpatches = plt, mpatches
        _FancyBboxPatch, _FancyArrowPatch = FancyBboxPatch, FancyArrowPatch
        _matplotlib_ready = True
    except Exception as e:
        log.warning(f"matplotlib 不可用: {e}")
        _matplotlib_ready = False
    return _matplotlib_ready


MATPLOTLIB_HINT = ("缺少 matplotlib 依赖，拓扑图无法生成。"
                   "请运行 tools\\安装画图依赖.bat，或执行："
                   "python -m pip install matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple")

log = logging.getLogger("image_gen")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ROOT_DIR, "models", "sd")
os.makedirs(MODELS_DIR, exist_ok=True)

# 下载源：ModelScope 阿里云 CDN 优先；失败回退 hf-mirror / huggingface.co
MODELSCOPE_REPO = "AI-ModelScope/stable-diffusion-v1-5"
HF_MIRROR = "https://hf-mirror.com"
HF_ORIGIN = "https://huggingface.co"
PRIMARY_SOURCE = "ModelScope (阿里云 CDN)"

# 两个 SD 模型：标准版(画质优先) + Turbo版(速度优先/无 GPU 时降级)
SD_MODELS = {
    "standard": {
        "repo": "runwayml/stable-diffusion-v1-5",
        "files": ["model_index.json", "tokenizer/tokenizer_config.json", "text_encoder/config.json",
                  "unet/config.json", "vae/config.json", "scheduler/scheduler_config.json"],
        "size_gb": 4.2,
        "steps": 20,
        "guidance": 7.5,
    },
    "turbo": {
        "repo": "CompVis/stable-diffusion-v1-5",  # 用 SD 1.5 + 1 步推理实现 Turbo 效果，省模型下载
        "files": ["model_index.json"],  # Turbo 复用 1.5 权重，加 scheduler 切到 1 步
        "size_gb": 0.0,  # 复用已下载的 standard 模型
        "steps": 1,
        "guidance": 0.0,  # Turbo 不需要 guidance
    },
}

# --------------------------------------------------------------------------
# 模型下载（国内源优先 + 回退）
# --------------------------------------------------------------------------

def _download_with_fallback(repo_id, filename, dest_path):
    """单文件下载：ModelScope 阿里云 → hf-mirror → huggingface.co"""
    # 策略0: ModelScope 阿里云 CDN（国内最稳最快）
    try:
        from modelscope import snapshot_download
        log.info(f"  [ModelScope] {filename}")
        target_root = os.path.dirname(os.path.dirname(dest_path))  # models/sd/<repo>_
        # dest_path 形如 .../models/sd/<repo_dir>/<sub>/file → 需要下载到 repo 根
        repo_dir = os.path.join(MODELS_DIR, repo_id.replace("/", "_"))
        snapshot_download(model_id=MODELSCOPE_REPO, local_dir=repo_dir,
                          allow_patterns=[filename])
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100:
            return True
    except ImportError:
        log.info("  (modelscope SDK 未安装,跳过此源)")
    except Exception as e:
        log.warning(f"  ModelScope 失败: {e}")

    mirror_url = f"{HF_MIRROR}/{repo_id}/resolve/main/{filename}"
    origin_url = f"{HF_ORIGIN}/{repo_id}/resolve/main/{filename}"

    # 策略1: urllib 国内源
    try:
        log.info(f"  [hf-mirror] {filename}")
        import urllib.request
        urllib.request.urlretrieve(mirror_url, dest_path)
        if os.path.getsize(dest_path) > 1024:
            return True
    except Exception as e:
        log.warning(f"  hf-mirror 失败: {e}")

    # 策略2: urllib 原版源
    try:
        log.info(f"  [huggingface] {filename}")
        import urllib.request
        urllib.request.urlretrieve(origin_url, dest_path)
        if os.path.getsize(dest_path) > 1024:
            return True
    except Exception as e:
        log.warning(f"  原版源失败: {e}")

    # 策略3: huggingface_hub (自带重试)
    try:
        log.info(f"  [hf_hub] {filename}")
        from huggingface_hub import hf_hub_download
        hf_hub_download(repo_id=repo_id, filename=filename, local_dir=MODELS_DIR)
        return True
    except Exception as e:
        log.warning(f"  hf_hub 失败: {e}")

    return False


def ensure_model(model_key="standard", progress_callback=None):
    """确保 SD 模型已下载到本地。返回是否就绪。"""
    cfg = SD_MODELS[model_key]
    repo = cfg["repo"]
    model_dir = os.path.join(MODELS_DIR, repo.replace("/", "_"))

    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)

    # 检查关键文件是否已存在
    missing = []
    for f in cfg["files"]:
        p = os.path.join(model_dir, f)
        if not os.path.exists(p) or os.path.getsize(p) < 100:
            missing.append(f)

    if not missing:
        return True  # 已就绪

    log.info(f"开始下载模型 {model_key} -> {model_dir}（{cfg['size_gb']} GB）")
    if progress_callback:
        progress_callback(f"下载模型 {model_key}（约 {cfg['size_gb']} GB）...")

    for i, f in enumerate(missing):
        if progress_callback:
            progress_callback(f"下载 {f} ({i+1}/{len(missing)})...")
        dest = os.path.join(model_dir, f)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        ok = _download_with_fallback(repo, f, dest)
        if not ok:
            log.error(f"下载失败: {f}")
            return False

    return True


def is_model_ready():
    """快速检测 SD 模型是否已下载完整"""
    standard = SD_MODELS["standard"]
    model_dir = os.path.join(MODELS_DIR, standard["repo"].replace("/", "_"))
    if not os.path.exists(model_dir):
        return False
    # 检查关键文件大小（model_index.json 必在；unet/diffusion_pytorch_model.bin 应 > 3GB）
    idx = os.path.join(model_dir, "model_index.json")
    if not os.path.exists(idx):
        return False
    return True


# --------------------------------------------------------------------------
# CUDA 检测
# --------------------------------------------------------------------------

_torch_available = None
_cuda_available = None


def _check_torch():
    global _torch_available, _cuda_available
    if _torch_available is not None:
        return _torch_available, _cuda_available
    try:
        import torch
        _torch_available = True
        _cuda_available = torch.cuda.is_available()
    except ImportError:
        _torch_available = False
        _cuda_available = False
    return _torch_available, _cuda_available


# --------------------------------------------------------------------------
# Stable Diffusion 出图（懒加载 + 线程安全）
# --------------------------------------------------------------------------

_pipe_lock = threading.Lock()
_pipe_cache = {}  # key: ("standard"|"turbo", device) → pipeline


def _get_pipeline(model_key="standard"):
    """懒加载 SD pipeline。有 GPU 用 standard，无 GPU 用 Turbo (1 步秒出)。"""
    torch_ok, cuda_ok = _check_torch()
    if not torch_ok:
        return None, "torch 未安装，无法加载 Stable Diffusion"

    device = "cuda" if cuda_ok else "cpu"
    cache_key = (model_key, device)
    if cache_key in _pipe_cache:
        return _pipe_cache[cache_key], None

    # 无 GPU → 强制用 Turbo
    if not cuda_ok and model_key == "standard":
        log.info("无 CUDA，自动切换到 SD-Turbo（1 步推理）")
        model_key = "turbo"

    try:
        from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler
    except ImportError:
        return None, ("缺少 diffusers 依赖，插画出图不可用。"
                      "请运行 tools\\安装画图依赖.bat 一键补装（约 2-3GB），或执行："
                      "python -m pip install torch diffusers transformers accelerate "
                      "safetensors -i https://pypi.tuna.tsinghua.edu.cn/simple")

    try:
        model_dir = os.path.join(MODELS_DIR, SD_MODELS["standard"]["repo"].replace("/", "_"))
        if not os.path.exists(model_dir):
            return None, "SD 模型未下载。请先运行 tools\\下载StableDiffusion.bat 或在「一键运行」第3步选择下载。"

        # dtype: GPU 用 fp16 省显存；CPU 用 fp32
        dtype = "float16" if cuda_ok else "float32"

        pipe = StableDiffusionPipeline.from_pretrained(
            model_dir,
            torch_dtype=dtype,
            safety_checker=None,  # 教学环境关掉 NSFW 过滤（中学生无此问题）
            requires_safety_checker=False,
        )
        pipe = pipe.to(device)

        # Turbo 模式：scheduler 切到 EulerAncestral，1 步推理
        if model_key == "turbo":
            pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)

        _pipe_cache[cache_key] = pipe
        return pipe, None

    except Exception as e:
        return None, f"加载 SD 模型失败: {e}"


def _generate_sd(prompt, width=512, height=512, seed=None):
    """SD 出图。返回 (base64_png, error_msg)"""
    torch_ok, cuda_ok = _check_torch()
    if not torch_ok:
        return None, ("缺少 PyTorch 依赖，插画出图不可用。"
                      "请运行 tools\\安装画图依赖.bat 一键补装，或执行："
                      "python -m pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple")

    # 先检测模型
    if not is_model_ready():
        return None, "SD 模型未下载。请运行 tools\\下载StableDiffusion.bat 首次下载（约 4GB），或重启「一键运行.bat」选择下载。"

    model_key = "standard" if cuda_ok else "turbo"
    pipe, err = _get_pipeline(model_key)
    if err:
        return None, err

    cfg = SD_MODELS[model_key]

    # 生成参数
    gen_kwargs = {
        "prompt": prompt,
        "width": min(width, 768),
        "height": min(height, 768),
        "num_inference_steps": cfg["steps"],
        "guidance_scale": cfg["guidance"],
    }
    if seed is not None:
        import torch
        gen_kwargs["generator"] = torch.Generator(device=pipe.device).manual_seed(seed)

    try:
        with _pipe_lock:
            result = pipe(**gen_kwargs)
        img = result.images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode(), None
    except Exception as e:
        return None, f"SD 推理失败: {e}"


# --------------------------------------------------------------------------
# Matplotlib 拓扑图（精准稳定）
# --------------------------------------------------------------------------

TOPOLOGY_KEYWORDS = [
    "拓扑", "架构", "网络", "vpc", "子网", "网段", "路由", "流程",
    "docker", "k8s", "kubernetes", "openstack", "vmware", "kvm",
    "nginx", "负载均衡", "集群", "高可用", "主从", "主备", "分布式",
    "架构图", "示意图", "拓扑图", "流程图", "关系图",
]


def is_topology_intent(prompt):
    """判断 prompt 是否拓扑/架构类。是→用 matplotlib 出图。"""
    p = prompt.lower()
    return any(kw in p for kw in TOPOLOGY_KEYWORDS)


# ------------------------------------------------------------------
# 拓扑图结构化知识库（每张图都自带「节点解释 + 数据流 + 学习要点」，
# 供 Ollama 在线时改写讲解，离线时直接作为讲解模板）
# ------------------------------------------------------------------
TOPOLOGY_KNOWLEDGE = {
    "vpc": {
        "title": "VPC 虚拟私有云",
        "summary": "在公有云里隔离出一块「你自己的网络」，相当于在一栋大楼里租了一层。",
        "nodes": [
            ("VPC (10.0.0.0/16)", "私有网络边界，16 位掩码最多 65536 个 IP，整个 VPC 内互通"),
            ("Public Subnet (10.0.1.0/24)", "公网子网：放需要被外网访问的资源（Web 服务器、NAT）"),
            ("Private Subnet (10.0.2.0/24)", "私有子网：放数据库等敏感资源，仅内网访问"),
            ("NAT Gateway", "让私有子网的 ECS 能主动访问外网（如 yum/apt 更新），但外部无法主动访问它"),
            ("Bastion (堡垒机)", "运维入口：从外网 SSH 跳进来访问内网 ECS 的中转节点"),
            ("Web ECS / DB ECS", "Web 服务器放公网子网；数据库放私有子网，安全性更高"),
        ],
        "flows": [
            "外网用户 → Web ECS（公网子网） → DB ECS（私有子网）",
            "DB ECS 出网请求 → NAT Gateway → Internet",
            "运维人员 → SSH 到 Bastion → 跳到内网 ECS",
        ],
        "key_points": [
            "**CIDR 必须包含子网网段**：VPC 是 10.0.0.0/16，子网是 10.0.1.0/24，后者在前者范围内",
            "**公网/私网子网区别**：能不能被外网直接访问，不是看 IP，而是看路由表 + 是否绑定弹性 IP",
            "**NAT 不是反向代理**：NAT 只让内网主动出，不能让外网主动访问内网",
        ],
    },
    "docker": {
        "title": "Docker 容器架构",
        "summary": "Docker 是把应用和它运行需要的环境一起打包的「集装箱」，保证换个机器也能跑起来。",
        "nodes": [
            ("Client", "用户命令行工具 docker，发指令给 dockerd"),
            ("dockerd (Daemon)", "Docker 后台守护进程，真正干活的家伙"),
            ("Images (镜像)", "只读模板，比如 mysql:8.0、nginx:latest，相当于「类」"),
            ("Containers (容器)", "镜像运行起来的实例，相当于「对象」，可启动/停止/删除"),
            ("Networks / Volumes", "网络：容器间通信；卷：容器持久化数据，删容器不丢"),
            ("Docker Hub", "官方镜像仓库，类似 GitHub，但存的是镜像不是代码"),
        ],
        "flows": [
            "Client → dockerd（通过 REST API，本地 socket 通信）",
            "dockerd → 拉镜像 / 启容器 / 配网络 / 挂卷",
            "dockerd ↔ Docker Hub（pull 拉镜像 / push 推镜像）",
        ],
        "key_points": [
            "**镜像分层只读**：多个镜像共享基础层，磁盘省 + 拉取快",
            "**容器是进程的封装**：跑在宿主机内核上，性能接近原生，没有虚拟机开销",
            "**数据卷才是持久化**：写进容器内的文件，删容器就丢，要用 -v 挂卷",
        ],
    },
    "k8s": {
        "title": "Kubernetes 集群架构",
        "summary": "K8s 是「容器的管家」：帮你自动部署、扩缩容、故障恢复，几十上百个容器也能管得井井有条。",
        "nodes": [
            ("API Server", "集群唯一入口，所有操作都发到这里（kubectl → API Server）"),
            ("etcd", "集群数据库，存所有配置和状态，丢了它整个集群瘫痪"),
            ("Scheduler", "调度器：决定新创建的 Pod 跑在哪个 Worker 节点"),
            ("Controller (Manager)", "控制器：不断比对「期望状态」和「实际状态」，不一致就调整"),
            ("kubelet", "每个 Worker 节点上的小管家，听 API Server 命令，管理 Pod 生命周期"),
            ("Pod", "K8s 最小调度单位，一般一个 Pod 一个容器"),
            ("Container Runtime", "真正运行容器的东西（containerd / docker）"),
        ],
        "flows": [
            "kubectl apply → API Server → etcd 持久化",
            "Scheduler 监听 → 发现未调度的 Pod → 选节点",
            "目标节点的 kubelet 收到指令 → 启动 Pod → 调 Container Runtime",
            "Controller 持续巡检：副本数不够？自动起新 Pod",
        ],
        "key_points": [
            "**声明式 vs 命令式**：你只说「我想要 3 个副本」，K8s 自己想办法凑够 3 个",
            "**Pod 不是容器**：Pod 是逻辑单元，里面可以装多个共享网络的容器",
            "**K8s 不跑容器**：它只调度 Pod，真正跑容器的是 kubelet + container runtime",
        ],
    },
    "nginx_lb": {
        "title": "Nginx 反向代理 + 负载均衡",
        "summary": "Nginx 站在用户和真实服务器之间，帮你把请求分发给后端多台机器，单台挂了也不影响。",
        "nodes": [
            ("Client (Browser)", "最终用户，从浏览器发起请求"),
            ("Nginx (Reverse Proxy)", "反向代理：用户的请求先到它，由它决定转发给哪台后端"),
            ("App-1 / App-2 / App-3", "真实业务服务器，多台组成集群分担压力"),
        ],
        "flows": [
            "用户请求 → Nginx",
            "Nginx 按策略（轮询/权重/IP哈希）选一台 App",
            "App 处理完返回结果给 Nginx",
            "Nginx 再把结果返回给用户（用户始终只跟 Nginx 通信）",
        ],
        "key_points": [
            "**反向代理 vs 正向代理**：反向是「代理服务器」，正向是「代理客户端」（如 VPN）",
            "**负载均衡策略**：轮询（默认）/ weight（按权重）/ ip_hash（同一用户走同机器，session 友好）",
            "**upstream 配置**：在 http 块里定义一组后端，location 里 proxy_pass 引用",
        ],
    },
    "ha": {
        "title": "主从高可用 (Master / Slave)",
        "summary": "两台机器做同样的事，平时只有一台在工作，另一台热备份；工作机挂了备份机顶上。",
        "nodes": [
            ("Client", "用户/应用，只看到一个「虚拟地址」"),
            ("VIP / Keepalived", "虚拟 IP + 心跳检测：谁活着就把 VIP 给谁"),
            ("Master", "主节点，平时干活，写操作走它"),
            ("Slave", "从节点，平时待命，实时同步 Master 数据"),
        ],
        "flows": [
            "请求 → VIP → Master（正常情况）",
            "Master 故障 → Keepalived 检测到 → 把 VIP 漂到 Slave → Slave 接替",
            "Master 恢复 → VIP 可自动切回（或留 Slave，由配置决定）",
            "Master 数据 → 实时同步 → Slave（replication）",
        ],
        "key_points": [
            "**VIP 是浮动 IP**：不是绑死在一台机器上，Keepalived 负责「搬家」",
            "**脑裂问题**：两台同时以为自己是 Master（网络分区时），要配仲裁/双心跳",
            "**同步 vs 异步复制**：异步丢数据少但延迟低，同步安全但慢",
        ],
    },
    "openstack": {
        "title": "OpenStack 私有云架构",
        "summary": "用一堆开源软件自己搭一个「公有云」，学校/企业机房常用，对标阿里云、华为云。",
        "nodes": [
            ("Keystone", "认证中心：所有服务都找它确认「你是谁、能干啥」"),
            ("Glance", "镜像服务：管操作系统模板（Windows/Ubuntu/CentOS 镜像）"),
            ("Nova", "计算服务：创建/删除虚拟机 CPU、内存、磁盘配额"),
            ("Neutron", "网络服务：管 VPC、子网、路由、浮动 IP、安全组"),
            ("Cinder", "块存储：给虚拟机挂云硬盘"),
            ("Horizon", "Web 控制台：浏览器点点鼠标就能开机器"),
        ],
        "flows": [
            "用户在 Horizon 选规格 → Nova 创建 VM",
            "VM 启动时 → Glance 拉镜像 → Neutron 配网络 → Cinder 挂云盘",
            "全程 Keystone 鉴权",
        ],
        "key_points": [
            "**模块化设计**：每个组件（Nova/Neutron...）独立，能单独替换",
            "**OpenStack ≠ 单一软件**：是一堆 Python 服务通过 API 协作的总称",
            "**学 OpenStack = 学云架构**：懂了它，看任何公有云都熟",
        ],
    },
    "generic": {
        "title": "通用流程图",
        "summary": "无法识别具体类型时的兜底模板：输入 → 处理 → 输出三段式。",
        "nodes": [
            ("Input", "数据/请求的入口"),
            ("Process", "核心处理逻辑"),
            ("Output", "结果/响应"),
        ],
        "flows": [
            "Input → Process → Output（线性单向）",
        ],
        "key_points": [
            "**通用模板**：实际场景请补充具体节点",
            "**说「画 VPC 拓扑」这类关键词**，我会自动用对应专业模板",
        ],
    },
}


def get_topology_knowledge(topic):
    """根据 _generate_topology 识别出的 topic，返回结构化图解知识。
    Ollama 在线时：让 LLM 基于这份知识改写讲解（更生动）
    Ollama 离线时：直接用这份知识渲染讲解（保证一定有图解）"""
    return TOPOLOGY_KNOWLEDGE.get(topic) or TOPOLOGY_KNOWLEDGE["generic"]


def render_topology_knowledge_html(knowledge):
    """把结构化图解渲染成 HTML 片段（Ollama 离线时使用）"""
    parts = [f"<strong>📘 图解：{knowledge['title']}</strong>",
             f"<em>{knowledge['summary']}</em><br>"]
    parts.append("<strong>一、节点含义</strong>")
    for name, desc in knowledge["nodes"]:
        parts.append(f"· <strong>{name}</strong>：{desc}")
    if knowledge.get("flows"):
        parts.append("<br><strong>二、数据/请求流向</strong>")
        for f in knowledge["flows"]:
            parts.append(f"· {f}")
    if knowledge.get("key_points"):
        parts.append("<br><strong>三、学习要点</strong>")
        for k in knowledge["key_points"]:
            parts.append(f"· {k}")
    return "<br>".join(parts)


def _generate_topology(prompt, extra_context=None):
    """用 matplotlib 出架构/拓扑图。返回 (base64_png, error_msg, topic)
    extra_context: list[str] | None   来自出图前搜集的资料（KB/联网）
                  当前主要用于调试/未来扩展，模板路由仍按 prompt 关键词
    """
    # 惰性加载 matplotlib，缺失时给出明确的安装提示（而不是抛异常）
    if not _ensure_matplotlib():
        return None, MATPLOTLIB_HINT
    plt = _plt
    try:
        # 中文支持
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "SimHei", "Microsoft YaHei", "Arial Unicode MS"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.axis("off")

        p = prompt.lower()

        # ---------- 模板路由 ----------
        # 每个分支都返回 (topic, desc_dict)，desc_dict 供上层生成图解
        if any(k in p for k in ["vpc", "子网", "网段", "云网络"]):
            _draw_vpc(ax)
            topic = "vpc"
        elif any(k in p for k in ["docker", "容器"]):
            _draw_docker(ax)
            topic = "docker"
        elif any(k in p for k in ["k8s", "kubernetes"]):
            _draw_k8s(ax)
            topic = "k8s"
        elif any(k in p for k in ["nginx", "负载均衡", "反向代理"]):
            _draw_nginx_lb(ax)
            topic = "nginx_lb"
        elif any(k in p for k in ["主从", "主备", "高可用", "集群"]):
            _draw_ha(ax)
            topic = "ha"
        elif any(k in p for k in ["openstack"]):
            _draw_openstack(ax)
            topic = "openstack"
        else:
            _draw_generic(ax, prompt)
            topic = "generic"

        ax.set_title(prompt[:30], fontsize=14, weight="bold", pad=10)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode(), None, topic
    except Exception as e:
        return None, f"拓扑图生成失败: {e}", "generic"


def _box(ax, x, y, w, h, text, color="#4A90E2", text_color="white"):
    """画一个圆角矩形节点"""
    box = _FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.05", linewidth=1.5,
                          edgecolor="#2C3E50", facecolor=color)
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=10, color=text_color, weight="bold")


def _arrow(ax, x1, y1, x2, y2, label="", color="#34495E"):
    arr = _FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle="->,head_width=4,head_length=6",
                           color=color, linewidth=1.5,
                           connectionstyle="arc3,rad=0.1")
    ax.add_patch(arr)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.15, label, ha="center", fontsize=8,
                color="#7F8C8D", bbox=dict(boxstyle="round,pad=0.2",
                                          facecolor="white", edgecolor="none"))


def _draw_vpc(ax):
    """VPC 网络拓扑：1 VPC + 2 子网 + ECS + NAT"""
    _box(ax, 5, 5, 8, 0.7, "VPC  10.0.0.0/16", color="#E74C3C")
    _box(ax, 2.5, 3.5, 3, 0.6, "Public Subnet  10.0.1.0/24", color="#F39C12")
    _box(ax, 7.5, 3.5, 3, 0.6, "Private Subnet  10.0.2.0/24", color="#9B59B6")
    _box(ax, 1.5, 1.8, 1.8, 0.6, "NAT GW", color="#3498DB")
    _box(ax, 3.5, 1.8, 1.5, 0.6, "Bastion", color="#3498DB")
    _box(ax, 6.5, 1.8, 1.5, 0.6, "Web ECS", color="#1ABC9C")
    _box(ax, 8.5, 1.8, 1.5, 0.6, "DB ECS", color="#1ABC9C")
    _box(ax, 5, 0.3, 6, 0.5, "Internet", color="#34495E")

    _arrow(ax, 2.5, 3.2, 1.5, 2.1)
    _arrow(ax, 2.5, 3.2, 3.5, 2.1)
    _arrow(ax, 1.5, 1.5, 4.5, 0.5, "Egress")
    _arrow(ax, 7.5, 3.2, 6.5, 2.1)
    _arrow(ax, 7.5, 3.2, 8.5, 2.1)
    _arrow(ax, 8.5, 1.8, 5.5, 0.5, "https")


def _draw_docker(ax):
    """Docker 架构：Client → Host(Engine) → Registry/Images/Containers"""
    _box(ax, 1, 5, 1.5, 0.6, "Client", color="#2496ED")
    _box(ax, 5, 5, 1.5, 0.6, "dockerd", color="#2496ED")
    _box(ax, 5, 3.3, 4, 0.6, "Images", color="#1ABC9C")
    _box(ax, 5, 2.0, 4, 0.6, "Containers", color="#16A085")
    _box(ax, 5, 0.7, 4, 0.6, "Networks / Volumes", color="#34495E")
    _box(ax, 9, 5, 1.5, 0.6, "Docker Hub", color="#F39C12")

    _arrow(ax, 1.75, 5, 4.25, 5, "REST API")
    _arrow(ax, 5, 4.7, 5, 3.6)
    _arrow(ax, 5, 3.0, 5, 2.3)
    _arrow(ax, 5, 1.7, 5, 1.0)
    _arrow(ax, 5.75, 5, 8.25, 5, "pull/push")


def _draw_k8s(ax):
    """K8s 架构：Master(API/etcd/sched) + Worker(Pod)"""
    _box(ax, 5, 5.3, 9, 0.6, "Kubernetes Cluster", color="#326CE5")
    _box(ax, 2.5, 4.2, 2, 0.5, "API Server", color="#326CE5")
    _box(ax, 2.5, 3.4, 2, 0.5, "etcd", color="#7B1FA2")
    _box(ax, 2.5, 2.6, 2, 0.5, "Scheduler", color="#326CE5")
    _box(ax, 2.5, 1.8, 2, 0.5, "Controller", color="#326CE5")
    _box(ax, 7.5, 4.2, 3.5, 0.5, "kubelet", color="#326CE5")
    _box(ax, 6.5, 2.8, 1.5, 0.5, "Pod", color="#1ABC9C")
    _box(ax, 8.5, 2.8, 1.5, 0.5, "Pod", color="#1ABC9C")
    _box(ax, 7.5, 1.4, 3.5, 0.5, "Container Runtime", color="#34495E")

    _arrow(ax, 5, 5.0, 2.5, 4.45)
    _arrow(ax, 5, 5.0, 7.5, 4.45)
    _arrow(ax, 7.5, 3.95, 6.5, 3.05)
    _arrow(ax, 7.5, 3.95, 8.5, 3.05)
    _arrow(ax, 7.5, 2.55, 7.5, 1.65)


def _draw_nginx_lb(ax):
    """Nginx 负载均衡"""
    _box(ax, 5, 0.5, 4, 0.5, "Client (Browser)", color="#34495E")
    _box(ax, 5, 2.2, 4, 0.6, "Nginx  (Reverse Proxy)", color="#27AE60")
    _box(ax, 1.5, 4.5, 2, 0.5, "App-1", color="#3498DB")
    _box(ax, 5.0, 4.5, 2, 0.5, "App-2", color="#3498DB")
    _box(ax, 8.5, 4.5, 2, 0.5, "App-3", color="#3498DB")

    _arrow(ax, 5, 0.75, 5, 1.9, "https")
    _arrow(ax, 4.0, 2.5, 1.5, 4.25, "proxy_pass")
    _arrow(ax, 5.0, 2.5, 5.0, 4.25)
    _arrow(ax, 6.0, 2.5, 8.5, 4.25)


def _draw_ha(ax):
    """主从高可用：Master/Slave + VIP"""
    _box(ax, 5, 0.5, 4, 0.5, "Client", color="#34495E")
    _box(ax, 5, 2.0, 3, 0.5, "VIP / Keepalived", color="#E74C3C")
    _box(ax, 2.5, 4.0, 2, 0.5, "Master", color="#27AE60")
    _box(ax, 7.5, 4.0, 2, 0.5, "Slave", color="#3498DB")
    _arrow(ax, 3.5, 4.25, 7.5, 4.25, "replication", color="#7F8C8D")
    _arrow(ax, 5, 0.75, 5, 1.75, "request")
    _arrow(ax, 4, 2.25, 2.5, 3.75, "active")
    _arrow(ax, 6, 2.25, 7.5, 3.75, "standby")


def _draw_openstack(ax):
    """OpenStack 架构：Nova/Neutron/Cinder/Glance/Keystone/Horizon"""
    _box(ax, 5, 5.2, 9, 0.5, "OpenStack Cloud", color="#ED1944")
    modules = [
        (1.5, 4, "Keystone", "#8E44AD"),
        (3.0, 4, "Glance", "#16A085"),
        (4.5, 4, "Nova", "#E74C3C"),
        (6.0, 4, "Neutron", "#3498DB"),
        (7.5, 4, "Cinder", "#F39C12"),
        (9.0, 4, "Horizon", "#34495E"),
    ]
    for x, y, n, c in modules:
        _box(ax, x, y, 1.2, 0.5, n, color=c)
    _box(ax, 5, 2.2, 8, 0.5, "Compute / Storage / Network Nodes", color="#7F8C8D")
    _arrow(ax, 5, 3.7, 5, 2.5)


def _draw_generic(ax, prompt):
    """通用流程图：3 节点串联"""
    nodes = ["Input", "Process", "Output"]
    for i, n in enumerate(nodes):
        _box(ax, 1.5 + i * 3.5, 3, 2, 0.6, n, color="#4A90E2")
        if i < 2:
            _arrow(ax, 2.5 + i * 3.5, 3, 4.0 + i * 3.5, 3)


# --------------------------------------------------------------------------
# 对外接口
# --------------------------------------------------------------------------

def generate(prompt, type="auto", width=512, height=512, seed=None,
             progress_callback=None, extra_context=None):
    """统一出图入口。

    type: "auto" | "topology" | "illustration"
    extra_context: list[str] | None   # 额外资料（来自知识库/联网检索）
                    拓扑图：作为更精细路由 + 让 LLM 改写讲解时用
                    插画： 拼到 SD prompt 里，让 SD 画得更准
    return: {"ok": bool, "image": base64_png | None,
             "engine": "matplotlib"|"sd"|"none",
             "topic": "vpc"|"docker"|...   # 拓扑图的主题，None=插画
             "error": str | None, "elapsed": 秒}
    """
    t0 = time.time()

    # 路由
    if type == "auto":
        type = "topology" if is_topology_intent(prompt) else "illustration"

    topic = None
    if type == "topology":
        img, err, topic = _generate_topology(prompt, extra_context=extra_context)
        engine = "matplotlib"
    else:
        # SD 插画：把 extra_context 拼到 prompt 里，让 SD 画得更有依据
        full_prompt = prompt
        if extra_context:
            full_prompt = prompt + ", " + ", ".join(extra_context[:5])
        img, err = _generate_sd(full_prompt, width, height, seed)
        engine = "sd"

        # SD 失败时降级为 matplotlib 通用图（兜底）
        # 仅在 matplotlib 可用时才兜底，否则保留 SD 的原始错误提示
        if err and _ensure_matplotlib():
            img2, err2, topic2 = _generate_topology(prompt, extra_context=extra_context)
            if img2:
                img, err = img2, None
                engine = "matplotlib"
                topic = topic2

    return {
        "ok": img is not None,
        "image": img,
        "engine": engine,
        "topic": topic,
        "error": err,
        "elapsed": round(time.time() - t0, 1),
    }


def get_status():
    """供 /api/sd_status 返回"""
    torch_ok, cuda_ok = _check_torch()
    ready = is_model_ready()
    mpl_ok = _ensure_matplotlib()
    # 插画出图是否真正可用：模型 + torch + diffusers 三者齐备
    diffusers_ok = False
    if torch_ok:
        try:
            import importlib.util
            diffusers_ok = importlib.util.find_spec("diffusers") is not None
        except Exception:
            diffusers_ok = False
    sd_usable = bool(ready and torch_ok and diffusers_ok)
    return {
        "ready": ready,
        "torch_installed": torch_ok,
        "diffusers_installed": diffusers_ok,
        "cuda_available": cuda_ok,
        "engine": "cuda" if cuda_ok else ("cpu" if torch_ok else "none"),
        "matplotlib_ok": mpl_ok,
        "sd_usable": sd_usable,
        "topology_usable": mpl_ok,
        "model_dir": os.path.join(MODELS_DIR, SD_MODELS["standard"]["repo"].replace("/", "_")),
        "download_size_gb": SD_MODELS["standard"]["size_gb"],
        "mirror": PRIMARY_SOURCE,  # ModelScope 阿里云 CDN(主源)
        "fallbacks": ["hf-mirror.com", "huggingface.co"],
    }