"""
Web Presentation Layer
Web表现层 - 包含Flask应用和所有与Web交互相关的实现

这个包只依赖 src/interface 层（桥接器层），
不依赖任何具体的 Agent 实现。

架构：
- src/interface/: 桥接器层（AgentService, AgentRegistry, AgentRouter）
- src/services/: Web表现层（Flask路由）
- src/agents/: 具体实现层（MockAgent 等）
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .flask_routes import create_app, run_app

__all__ = [
    "create_app",
    "run_app",
]
