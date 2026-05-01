"""
Agent注册中心接口定义

注册中心负责管理所有Agent的生命周期，
包括注册、注销、查询和实例化。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable, Protocol, runtime_checkable

from .data_models import AgentDescriptor, AgentInfo


@runtime_checkable
class IAgentRegistry(Protocol):
    """
    Agent注册中心接口协议
    
    职责：
    1. 注册/注销Agent
    2. 查询Agent信息
    3. 懒加载Agent实例
    4. 依赖检查
    """
    
    @abstractmethod
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
        注册一个Agent
        
        Args:
            agent_id: Agent唯一标识
            name: Agent名称
            description: Agent描述
            agent_class: Agent类（用于实例化）
            capabilities: 能力列表
            dependencies: 依赖列表（Python模块名）
            factory: 工厂函数（优先级高于agent_class）
            enabled: 是否启用
            priority: 优先级（用于排序）
        
        Returns:
            AgentDescriptor: Agent描述符
        """
        ...
    
    @abstractmethod
    def unregister(self, agent_id: str) -> bool:
        """
        注销一个Agent
        
        Args:
            agent_id: Agent唯一标识
        
        Returns:
            bool: 是否成功注销
        """
        ...
    
    @abstractmethod
    def get(self, agent_id: str) -> Optional[Any]:
        """
        获取Agent实例（懒加载）
        
        Args:
            agent_id: Agent唯一标识
        
        Returns:
            Optional[Any]: Agent实例，不可用则返回None
        """
        ...
    
    @abstractmethod
    def get_descriptor(self, agent_id: str) -> Optional[AgentDescriptor]:
        """
        获取Agent描述符
        
        Args:
            agent_id: Agent唯一标识
        
        Returns:
            Optional[AgentDescriptor]: Agent描述符
        """
        ...
    
    @abstractmethod
    def list_agents(self, include_disabled: bool = False) -> List[AgentDescriptor]:
        """
        列出所有注册的Agent
        
        Args:
            include_disabled: 是否包含禁用的Agent
        
        Returns:
            List[AgentDescriptor]: Agent描述符列表
        """
        ...
    
    @abstractmethod
    def list_agent_info(self, include_disabled: bool = False) -> List[AgentInfo]:
        """
        列出所有Agent的信息（用于前端展示）
        
        Args:
            include_disabled: 是否包含禁用的Agent
        
        Returns:
            List[AgentInfo]: Agent信息列表
        """
        ...
    
    @abstractmethod
    def find_by_capability(self, capability: str) -> List[AgentDescriptor]:
        """
        根据能力查找Agent
        
        Args:
            capability: 能力名称
        
        Returns:
            List[AgentDescriptor]: 具备该能力的Agent列表
        """
        ...
    
    @abstractmethod
    def is_available(self, agent_id: str) -> bool:
        """
        检查Agent是否可用
        
        Args:
            agent_id: Agent唯一标识
        
        Returns:
            bool: 是否可用
        """
        ...
    
    @abstractmethod
    def enable(self, agent_id: str) -> bool:
        """
        启用Agent
        
        Args:
            agent_id: Agent唯一标识
        
        Returns:
            bool: 是否成功
        """
        ...
    
    @abstractmethod
    def disable(self, agent_id: str) -> bool:
        """
        禁用Agent
        
        Args:
            agent_id: Agent唯一标识
        
        Returns:
            bool: 是否成功
        """
        ...


class BaseAgentRegistry(ABC):
    """
    Agent注册中心抽象基类
    
    提供通用实现框架。
    """
    
    @abstractmethod
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
        ...
    
    @abstractmethod
    def unregister(self, agent_id: str) -> bool:
        ...
    
    @abstractmethod
    def get(self, agent_id: str) -> Optional[Any]:
        ...
    
    def get_descriptor(self, agent_id: str) -> Optional[AgentDescriptor]:
        for desc in self.list_agents(include_disabled=True):
            if desc.agent_id == agent_id:
                return desc
        return None
    
    @abstractmethod
    def list_agents(self, include_disabled: bool = False) -> List[AgentDescriptor]:
        ...
    
    def list_agent_info(self, include_disabled: bool = False) -> List[AgentInfo]:
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
        return [
            desc for desc in self.list_agents()
            if capability in desc.capabilities
        ]
    
    def is_available(self, agent_id: str) -> bool:
        descriptor = self.get_descriptor(agent_id)
        if descriptor is None:
            return False
        return descriptor.is_available()
    
    def enable(self, agent_id: str) -> bool:
        descriptor = self.get_descriptor(agent_id)
        if descriptor:
            descriptor.enabled = True
            return True
        return False
    
    def disable(self, agent_id: str) -> bool:
        descriptor = self.get_descriptor(agent_id)
        if descriptor:
            descriptor.enabled = False
            return True
        return False
