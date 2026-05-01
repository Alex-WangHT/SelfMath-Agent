import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

from dotenv import load_dotenv

from src.agents.base_agent import AgentRole
from src.agents.question_bank_agent import QuestionBankManagementAgent
from src.prompts import PromptManager

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AgentSession:
    session_id: str
    agent_role: AgentRole
    created_at: datetime = field(default_factory=datetime.now)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentManager:
    """
    Agent 管理器
    
    职责：
    1. 管理多个 Agent 实例的生命周期
    2. 路由用户请求到合适的 Agent
    3. 管理会话状态
    4. 提供统一的接口与 Web 层交互
    
    设计原则：
    - 与 Web 层完全解耦
    - 支持多种 Agent 类型
    - 支持会话管理
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, prompts_path: Optional[str] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        
        self.prompts_path = prompts_path or os.getenv("PROMPTS_PATH", "./prompts.json")
        self.prompt_manager = PromptManager(self.prompts_path)
        
        self.agents: Dict[AgentRole, Any] = {}
        self.sessions: Dict[str, AgentSession] = {}
        
        self._init_agents()
        
        logger.info("AgentManager initialized successfully")
    
    def _init_agents(self):
        """初始化所有可用的 Agent"""
        try:
            self.agents[AgentRole.QUESTION_BANK] = QuestionBankManagementAgent(
                prompt_manager=self.prompt_manager
            )
            logger.info("QuestionBankManagementAgent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize QuestionBankManagementAgent: {e}")
    
    def get_agent(self, agent_role: Optional[AgentRole] = None) -> Any:
        """
        获取指定类型的 Agent
        
        Args:
            agent_role: Agent 角色枚举
            
        Returns:
            Agent 实例
        """
        if agent_role is None:
            agent_role = AgentRole.QUESTION_BANK
        
        if agent_role in self.agents:
            return self.agents[agent_role]
        
        raise ValueError(f"Agent not found for role: {agent_role}")
    
    def chat(
        self,
        user_message: str,
        agent_role: Optional[AgentRole] = None,
        session_id: Optional[str] = None,
        context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        处理用户聊天请求
        
        Args:
            user_message: 用户消息
            agent_role: 指定使用的 Agent 角色
            session_id: 会话 ID
            context: 上下文信息
            
        Returns:
            包含响应内容的字典
        """
        try:
            agent = self.get_agent(agent_role)
            actual_role = agent_role or AgentRole.QUESTION_BANK
            
            session_id = session_id or f"default_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            if session_id not in self.sessions:
                self.sessions[session_id] = AgentSession(
                    session_id=session_id,
                    agent_role=actual_role
                )
            
            session = self.sessions[session_id]
            
            session.conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            try:
                response = agent.run(user_message)
            except Exception as e:
                logger.error(f"Agent chat error: {e}")
                response = f"抱歉，处理您的请求时出错：{str(e)}"
            
            session.conversation_history.append({
                "role": "assistant",
                "content": response,
                "agent_role": actual_role.value,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "content": response,
                "agent_role": actual_role.value,
                "session_id": session_id,
                "metadata": {
                    "conversation_length": len(session.conversation_history)
                }
            }
            
        except Exception as e:
            logger.error(f"Chat error in AgentManager: {e}")
            return {
                "content": f"处理请求时出错：{str(e)}",
                "agent_role": (agent_role or AgentRole.QUESTION_BANK).value,
                "error": str(e)
            }
    
    def process_pdf(
        self,
        pdf_path: str,
        start_page: int = 0,
        end_page: Optional[int] = None,
        session_id: Optional[str] = None,
        enable_cross_page_merge: bool = True,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        处理 PDF 文件
        
        Args:
            pdf_path: PDF 文件路径
            start_page: 起始页码
            end_page: 结束页码
            session_id: 会话 ID
            enable_cross_page_merge: 是否启用跨页合并
            auto_save: 是否自动保存到题库
            
        Returns:
            处理结果
        """
        try:
            agent = self.get_agent(AgentRole.QUESTION_BANK)
            
            if not hasattr(agent, 'process_pdf'):
                raise ValueError("QuestionBankManagementAgent does not support PDF processing")
            
            questions = agent.process_pdf(
                pdf_path=pdf_path,
                start_page=start_page,
                end_page=end_page,
                enable_cross_page_merge=enable_cross_page_merge,
                auto_save=auto_save
            )
            
            stats = agent.get_stats() if hasattr(agent, 'get_stats') else {}
            
            example_count = sum(1 for q in questions if q.get('question_type') == 'example')
            exercise_count = len(questions) - example_count
            with_solution_count = sum(1 for q in questions if q.get('has_solution') or q.get('solution_content'))
            
            return {
                "success": True,
                "total_questions": len(questions),
                "example_count": example_count,
                "exercise_count": exercise_count,
                "with_solution_count": with_solution_count,
                "questions": questions,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_questions": 0
            }
    
    def process_image(
        self,
        image_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理图片文件
        
        Args:
            image_path: 图片路径
            session_id: 会话 ID
            
        Returns:
            处理结果
        """
        try:
            agent = self.get_agent(AgentRole.QUESTION_BANK)
            
            ocr_text = ""
            questions = []
            
            if hasattr(agent, '_ocr_image_with_solution_tool'):
                ocr_text = agent._ocr_image_with_solution_tool.invoke({"image_path": image_path})
            
            if hasattr(agent, '_parse_questions_with_solution_tool') and ocr_text:
                questions = agent._parse_questions_with_solution_tool.invoke({"ocr_text": ocr_text})
            
            return {
                "success": True,
                "ocr_text": ocr_text,
                "questions": questions,
                "question_count": len(questions)
            }
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "ocr_text": "",
                "questions": []
            }
    
    def get_all_questions(
        self,
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取所有题目
        
        Args:
            question_type: 题目类型过滤
            
        Returns:
            题目列表
        """
        try:
            agent = self.get_agent(AgentRole.QUESTION_BANK)
            
            if hasattr(agent, 'get_all_questions'):
                return agent.get_all_questions(question_type=question_type)
            
            return []
            
        except Exception as e:
            logger.error(f"Get questions error: {e}")
            return []
    
    def search_questions(
        self,
        query: str,
        n_results: int = 5,
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索题目
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            question_type: 题目类型过滤
            
        Returns:
            搜索结果
        """
        try:
            agent = self.get_agent(AgentRole.QUESTION_BANK)
            
            if hasattr(agent, 'search_questions'):
                return agent.search_questions(
                    query=query,
                    n_results=n_results,
                    question_type=question_type
                )
            
            return []
            
        except Exception as e:
            logger.error(f"Search questions error: {e}")
            return []
    
    def get_question_stats(self) -> Dict[str, Any]:
        """
        获取题库统计
        
        Returns:
            统计信息
        """
        try:
            agent = self.get_agent(AgentRole.QUESTION_BANK)
            
            if hasattr(agent, 'get_stats'):
                return agent.get_stats()
            
            return {}
            
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return {}
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的 Agent
        
        Returns:
            Agent 信息列表
        """
        agents_info = []
        
        for role, agent in self.agents.items():
            info = {
                "role": role.value,
                "name": agent.__class__.__name__,
                "tools": [],
                "status": "active"
            }
            
            if hasattr(agent, 'get_tool_names'):
                info["tools"] = agent.get_tool_names()
            
            agents_info.append(info)
        
        return agents_info
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """
        获取会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话实例
        """
        return self.sessions.get(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """
        清除会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否成功
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def reload_prompts(self) -> None:
        """重新加载提示词"""
        self.prompt_manager.reload()
        
        for agent in self.agents.values():
            if hasattr(agent, 'reload_prompts'):
                agent.reload_prompts()
        
        logger.info("All agents reloaded with new prompts")
