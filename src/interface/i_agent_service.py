"""
Agent服务接口定义

这是Web层与Agent层之间的核心接口协议。
所有Agent服务实现都必须遵守这个接口。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable

from .data_models import (
    AgentResponse,
    AgentInfo,
    Question,
    QuestionStats,
    UploadResult,
    Conversation,
)


@runtime_checkable
class IAgentService(Protocol):
    """
    Agent服务接口协议
    
    这是Web层唯一需要知道的接口。
    所有具体实现（Mock或真实Agent）都必须实现这个接口。
    """
    
    @abstractmethod
    def chat(
        self,
        message: str,
        agent_type: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        处理聊天请求
        
        Args:
            message: 用户消息内容
            agent_type: 指定的Agent类型，或 "auto" 自动选择
            conversation_id: 对话ID
            context: 上下文信息
        
        Returns:
            AgentResponse: Agent响应
        """
        ...
    
    @abstractmethod
    def list_agents(self) -> List[AgentInfo]:
        """
        列出所有可用的Agent
        
        Returns:
            List[AgentInfo]: Agent信息列表
        """
        ...
    
    @abstractmethod
    def get_agent_capabilities(self, agent_type: str) -> List[str]:
        """
        获取指定Agent的能力列表
        
        Args:
            agent_type: Agent类型
        
        Returns:
            List[str]: 能力列表
        """
        ...
    
    @abstractmethod
    def process_pdf(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        """
        处理PDF文件
        
        Args:
            file_path: 文件路径
            options: 处理选项（start_page, end_page 等）
        
        Returns:
            UploadResult: 处理结果
        """
        ...
    
    @abstractmethod
    def process_image(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        """
        处理图片文件
        
        Args:
            file_path: 文件路径
            options: 处理选项
        
        Returns:
            UploadResult: 处理结果
        """
        ...
    
    @abstractmethod
    def get_all_questions(
        self,
        question_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Question]:
        """
        获取所有题目
        
        Args:
            question_type: 题目类型过滤（example/exercise）
            limit: 返回数量限制
        
        Returns:
            List[Question]: 题目列表
        """
        ...
    
    @abstractmethod
    def search_questions(
        self,
        query: str,
        n_results: int = 10,
        question_type: Optional[str] = None
    ) -> List[Question]:
        """
        搜索题目
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            question_type: 题目类型过滤
        
        Returns:
            List[Question]: 搜索结果
        """
        ...
    
    @abstractmethod
    def get_question_stats(self) -> QuestionStats:
        """
        获取题库统计
        
        Returns:
            QuestionStats: 统计信息
        """
        ...
    
    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        获取对话历史
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            Optional[Conversation]: 对话对象，不存在则返回None
        """
        ...
    
    @abstractmethod
    def clear_conversation(self, conversation_id: str) -> bool:
        """
        清除对话
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            bool: 是否成功
        """
        ...
    
    @abstractmethod
    def is_agent_available(self, agent_type: str) -> bool:
        """
        检查Agent是否可用
        
        Args:
            agent_type: Agent类型
        
        Returns:
            bool: 是否可用
        """
        ...


class BaseAgentService(ABC):
    """
    Agent服务抽象基类
    
    提供一些通用的实现，具体实现可以继承这个类。
    """
    
    @abstractmethod
    def chat(
        self,
        message: str,
        agent_type: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        ...
    
    @abstractmethod
    def list_agents(self) -> List[AgentInfo]:
        ...
    
    def get_agent_capabilities(self, agent_type: str) -> List[str]:
        agents = self.list_agents()
        for agent in agents:
            if agent.agent_id == agent_type:
                return agent.capabilities
        return []
    
    @abstractmethod
    def process_pdf(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        ...
    
    @abstractmethod
    def process_image(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        ...
    
    @abstractmethod
    def get_all_questions(
        self,
        question_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Question]:
        ...
    
    @abstractmethod
    def search_questions(
        self,
        query: str,
        n_results: int = 10,
        question_type: Optional[str] = None
    ) -> List[Question]:
        ...
    
    @abstractmethod
    def get_question_stats(self) -> QuestionStats:
        ...
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return None
    
    def clear_conversation(self, conversation_id: str) -> bool:
        return False
    
    def is_agent_available(self, agent_type: str) -> bool:
        agents = self.list_agents()
        return any(a.agent_id == agent_type for a in agents)
