"""
Agent注册中心实现

负责管理所有Agent的生命周期，
包括注册、注销、查询和实例化。
"""
import logging
from typing import Dict, Any, List, Optional, Type, Callable

from src.interface import (
    AgentDescriptor,
    AgentInfo,
    IAgentRegistry,
    BaseAgentRegistry,
)

logger = logging.getLogger(__name__)


class AgentRegistry(BaseAgentRegistry):
    """
    Agent注册中心
    
    这是一个单例实现，确保全局只有一个注册中心实例。
    
    功能：
    1. 管理所有Agent的元数据
    2. 懒加载Agent实例
    3. 支持动态注册/注销
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
        
        self._agents: Dict[str, AgentDescriptor] = {}
        self._initialized = True
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
        """注册一个Agent"""
        
        if agent_id in self._agents:
            logger.warning(f"Agent {agent_id} already registered, overwriting")
        
        descriptor = AgentDescriptor(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=capabilities or [],
            dependencies=dependencies or [],
            enabled=enabled,
            priority=priority,
            agent_class=agent_class,
            factory=factory,
        )
        
        self._agents[agent_id] = descriptor
        logger.info(f"Registered agent: {agent_id} ({name})")
        
        return descriptor
    
    def unregister(self, agent_id: str) -> bool:
        """注销一个Agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False
    
    def get(self, agent_id: str) -> Optional[Any]:
        """
        获取Agent实例（懒加载）
        
        优先使用工厂函数，其次使用类实例化。
        """
        descriptor = self._agents.get(agent_id)
        
        if descriptor is None:
            logger.warning(f"Agent not found: {agent_id}")
            return None
        
        if not descriptor.enabled:
            logger.warning(f"Agent is disabled: {agent_id}")
            return None
        
        # 检查依赖
        for dep in descriptor.dependencies:
            if not self._check_dependency(dep):
                logger.error(f"Missing dependency for {agent_id}: {dep}")
                return None
        
        # 懒加载实例
        if descriptor.instance is None:
            try:
                if descriptor.factory:
                    descriptor.instance = descriptor.factory()
                elif descriptor.agent_class:
                    descriptor.instance = descriptor.agent_class()
                else:
                    # 没有工厂函数也没有类，返回None
                    logger.warning(f"Agent {agent_id} has no factory or class")
                    return None
                
                logger.info(f"Instantiated agent: {agent_id}")
            except Exception as e:
                logger.error(f"Failed to instantiate {agent_id}: {e}")
                return None
        
        return descriptor.instance
    
    def _check_dependency(self, dep: str) -> bool:
        """检查依赖模块是否可用"""
        try:
            __import__(dep)
            return True
        except ImportError:
            return False
    
    def get_descriptor(self, agent_id: str) -> Optional[AgentDescriptor]:
        """获取Agent描述符"""
        return self._agents.get(agent_id)
    
    def list_agents(self, include_disabled: bool = False) -> List[AgentDescriptor]:
        """列出所有注册的Agent（按优先级排序）"""
        agents = [
            desc for desc in self._agents.values()
            if include_disabled or desc.enabled
        ]
        return sorted(agents, key=lambda x: -x.priority)
    
    def list_agent_info(self, include_disabled: bool = False) -> List[AgentInfo]:
        """列出所有Agent的信息（用于前端展示）"""
        descriptors = self.list_agents(include_disabled)
        
        icon_map = {
            "question_bank": "bi-database",
            "understanding": "bi-lightbulb",
            "verification": "bi-check-circle",
            "planning": "bi-calendar-check",
            "assessment": "bi-graph-up",
            "learning": "bi-book",
            "orchestrator": "bi-people",
        }
        
        return [
            AgentInfo(
                agent_id=desc.agent_id,
                name=desc.name,
                description=desc.description,
                capabilities=desc.capabilities,
                icon=icon_map.get(desc.agent_id, "bi-robot"),
                status="active" if desc.enabled else "disabled"
            )
            for desc in descriptors
        ]
    
    def find_by_capability(self, capability: str) -> List[AgentDescriptor]:
        """根据能力查找Agent"""
        return [
            desc for desc in self._agents.values()
            if desc.enabled and capability in desc.capabilities
        ]
    
    def is_available(self, agent_id: str) -> bool:
        """检查Agent是否可用"""
        descriptor = self._agents.get(agent_id)
        if descriptor is None:
            return False
        if not descriptor.enabled:
            return False
        for dep in descriptor.dependencies:
            if not self._check_dependency(dep):
                return False
        return True
    
    def enable(self, agent_id: str) -> bool:
        """启用Agent"""
        descriptor = self._agents.get(agent_id)
        if descriptor:
            descriptor.enabled = True
            logger.info(f"Enabled agent: {agent_id}")
            return True
        return False
    
    def disable(self, agent_id: str) -> bool:
        """禁用Agent"""
        descriptor = self._agents.get(agent_id)
        if descriptor:
            descriptor.enabled = False
            logger.info(f"Disabled agent: {agent_id}")
            return True
        return False
    
    def clear(self) -> None:
        """清空所有注册的Agent"""
        self._agents.clear()
        logger.info("AgentRegistry cleared")


def get_registry() -> AgentRegistry:
    """获取注册中心单例"""
    return AgentRegistry()


def register_agent(
    agent_id: str,
    name: str,
    description: str,
    agent_class: Optional[Type[Any]] = None,
    **kwargs
) -> AgentDescriptor:
    """便捷函数：注册Agent"""
    return get_registry().register(
        agent_id=agent_id,
        name=name,
        description=description,
        agent_class=agent_class,
        **kwargs
    )
