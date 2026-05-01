"""
Web Presentation Layer
Web表现层 - 包含Flask应用和所有与Web交互相关的实现

这个包只依赖 src/interface 层，
不依赖任何具体的Agent实现。
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .agent_registry import AgentRegistry, get_registry, register_agent
from .agent_router import AgentRouter, SimpleKeywordRouter
from .mock_service import MockAgentService
from .flask_routes import create_app, run_app

__all__ = [
    "AgentRegistry",
    "get_registry",
    "register_agent",
    "AgentRouter",
    "SimpleKeywordRouter",
    "MockAgentService",
    "create_app",
    "run_app",
]
