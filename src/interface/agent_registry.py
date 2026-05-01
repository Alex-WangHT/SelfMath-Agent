"""
Agent注册中心（桥接器）

这是 Web 层和具体 Agent 实现之间的桥梁。
提供统一的 Agent 注册、查询和实例化接口。
"""
import logging
from typing import Dict, Any, List, Optional, Type, Callable

from .data_models import AgentDescriptor, AgentInfo


logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Agent注册中心
    
    职责：
    1. 注册/注销 Agent
    2. 查询 Agent 信息
    3. 懒加载 Agent 实例
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._agents: Dict[str, AgentDescriptor] = {}
        self._instances: Dict[str, Any] = {}
        
        logger.info("AgentRegistry initialized")
    
    def register(
        self,
        agent_id: str,
        name: str,
        description: str,
        agent_class: Optional[Type[Any]] = None,
        capabilities: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        factory: Optional[Callable[..., Any]] = None,
        enabled: bool = True,
        priority: int = 0
    ) -> AgentDescriptor:
        """
        注册一个 Agent
        
        Args:
            agent_id: Agent 唯一标识
            name: Agent 名称
            description: Agent 描述
            agent_class: Agent 类（用于实例化）
            capabilities: 能力列表
            dependencies: 依赖列表
            factory: 工厂函数（优先级高于 agent_class）
            enabled: 是否启用
            priority: 优先级
        
        Returns:
            AgentDescriptor: Agent 描述符
        """
        descriptor = AgentDescriptor(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=capabilities or [],
            dependencies=dependencies or [],
            enabled=enabled,
            priority=priority,
            factory=factory
        )
        
        self._agents[agent_id] = descriptor
        logger.info(f"Agent registered: {agent_id} ({name})")
        
        return descriptor
    
    def unregister(self, agent_id: str) -> bool:
        """注销一个 Agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            if agent_id in self._instances:
                del self._instances[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
            return True
        return False
    
    def get(self, agent_id: str) -> Optional[Any]:
        """
        获取 Agent 实例（懒加载）
        
        Args:
            agent_id: Agent 唯一标识
        
        Returns:
            Optional[Any]: Agent 实例，不可用则返回 None
        """
        if agent_id not in self._agents:
            return None
        
        descriptor = self._agents[agent_id]
        
        if not descriptor.is_available():
            return None
        
        if agent_id in self._instances:
            return self._instances[agent_id]
        
        if descriptor.factory:
            try:
                instance = descriptor.factory()
                self._instances[agent_id] = instance
                logger.info(f"Agent instance created: {agent_id}")
                return instance
            except Exception as e:
                logger.error(f"Failed to create agent instance {agent_id}: {e}")
                return None
        
        return None
    
    def get_descriptor(self, agent_id: str) -> Optional[AgentDescriptor]:
        """获取 Agent 描述符"""
        return self._agents.get(agent_id)
    
    def list_agents(self, include_disabled: bool = False) -> List[AgentDescriptor]:
        """列出所有注册的 Agent"""
        if include_disabled:
            return list(self._agents.values())
        return [desc for desc in self._agents.values() if desc.enabled]
    
    def list_agent_info(self, include_disabled: bool = False) -> List[AgentInfo]:
        """列出所有 Agent 的信息（用于前端展示）"""
        descriptors = self.list_agents(include_disabled)
        return [
            AgentInfo(
                agent_id=desc.agent_id,
                name=desc.name,
                description=desc.description,
                capabilities=desc.capabilities,
                status="active" if desc.enabled else "disabled"
            )
            for desc in descriptors
        ]
    
    def find_by_capability(self, capability: str) -> List[AgentDescriptor]:
        """根据能力查找 Agent"""
        return [
            desc for desc in self.list_agents()
            if capability in desc.capabilities
        ]
    
    def is_available(self, agent_id: str) -> bool:
        """检查 Agent 是否可用"""
        descriptor = self.get_descriptor(agent_id)
        if descriptor is None:
            return False
        return descriptor.is_available()
    
    def enable(self, agent_id: str) -> bool:
        """启用 Agent"""
        descriptor = self.get_descriptor(agent_id)
        if descriptor:
            descriptor.enabled = True
            logger.info(f"Agent enabled: {agent_id}")
            return True
        return False
    
    def disable(self, agent_id: str) -> bool:
        """禁用 Agent"""
        descriptor = self.get_descriptor(agent_id)
        if descriptor:
            descriptor.enabled = False
            logger.info(f"Agent disabled: {agent_id}")
            return True
        return False
    
    def clear(self):
        """清空所有注册的 Agent"""
        self._agents.clear()
        self._instances.clear()
        logger.info("AgentRegistry cleared")


def get_registry() -> AgentRegistry:
    """获取注册中心单例"""
    return AgentRegistry()


def register_agent(
    agent_id: str,
    name: str,
    description: str,
    capabilities: Optional[List[str]] = None,
    factory: Optional[Callable[..., Any]] = None,
    priority: int = 0
) -> AgentDescriptor:
    """
    便捷函数：注册一个 Agent
    
    Args:
        agent_id: Agent 唯一标识
        name: Agent 名称
        description: Agent 描述
        capabilities: 能力列表
        factory: 工厂函数
        priority: 优先级
    
    Returns:
        AgentDescriptor: Agent 描述符
    """
    registry = get_registry()
    return registry.register(
        agent_id=agent_id,
        name=name,
        description=description,
        capabilities=capabilities,
        factory=factory,
        priority=priority
    )
