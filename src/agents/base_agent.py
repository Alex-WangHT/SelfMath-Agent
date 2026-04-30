import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool

from src.prompts import PromptManager

logger = logging.getLogger(__name__)

load_dotenv()


class BaseAgent(ABC):
    """
    Agent 基类，定义所有 Agent 的通用接口和行为
    
    子类需要实现：
    - _create_tools(): 创建 Agent 特定的工具列表
    - _get_system_prompt(): 获取 Agent 的系统提示词
    """
    
    def __init__(
        self,
        prompt_manager: Optional[PromptManager] = None,
        prompts_path: Optional[str] = None,
        agent_name: str = "base_agent"
    ):
        """
        初始化 Agent 基类
        
        Args:
            prompt_manager: 提示词管理器，如果为 None 则自动创建
            prompts_path: 提示词文件路径，仅在 prompt_manager 为 None 时使用
            agent_name: Agent 名称，用于标识不同的 Agent
        """
        self.agent_name = agent_name
        self.prompt_manager = prompt_manager or PromptManager(prompts_path)
        
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        self.base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        self.model = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen3-Omni-30B-A3B-Captioner")
        
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent_executor()
        
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment variables")
        
        logger.info(f"{self.agent_name} initialized successfully")
    
    @abstractmethod
    def _create_tools(self) -> List[BaseTool]:
        """
        创建 Agent 特定的工具列表
        
        子类必须实现此方法，返回该 Agent 可用的工具列表
        
        Returns:
            工具列表
        """
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """
        获取 Agent 的系统提示词
        
        子类必须实现此方法，返回该 Agent 的系统提示词
        
        Returns:
            系统提示词字符串
        """
        pass
    
    def _create_agent_executor(self) -> AgentExecutor:
        """
        创建 Agent 执行器
        
        使用 LangChain 的 AgentExecutor 包装 Agent
        
        Returns:
            AgentExecutor 实例
        """
        system_prompt = self._get_system_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("agent_scratchpad", "{agent_scratchpad}")
        ])
        
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.0
        )
        
        agent = create_tool_calling_agent(llm, self.tools, prompt)
        
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def invoke(self, input: str, **kwargs) -> Dict[str, Any]:
        """
        调用 Agent 执行任务
        
        Args:
            input: 用户输入
            **kwargs: 额外的参数
            
        Returns:
            Agent 执行结果
        """
        logger.info(f"{self.agent_name} invoking with input: {input[:50]}...")
        return self.agent_executor.invoke({"input": input, **kwargs})
    
    def run(self, input: str, **kwargs) -> str:
        """
        运行 Agent（简化接口）
        
        Args:
            input: 用户输入
            **kwargs: 额外的参数
            
        Returns:
            Agent 输出结果
        """
        result = self.invoke(input, **kwargs)
        return result.get("output", "")
    
    def get_tools(self) -> List[BaseTool]:
        """
        获取 Agent 的工具列表
        
        Returns:
            工具列表
        """
        return self.tools
    
    def get_tool_names(self) -> List[str]:
        """
        获取工具名称列表
        
        Returns:
            工具名称列表
        """
        return [tool.name for tool in self.tools]
    
    def reload_prompts(self) -> None:
        """
        重新加载提示词
        
        当提示词文件被修改后，可以调用此方法刷新
        """
        self.prompt_manager.reload()
        self.agent_executor = self._create_agent_executor()
        logger.info(f"{self.agent_name} prompts reloaded")
