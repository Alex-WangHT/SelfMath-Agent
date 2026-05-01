import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MockAgentSession:
    session_id: str
    agent_role: str
    created_at: datetime = field(default_factory=datetime.now)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MockAgentManager:
    """
    Mock Agent 管理器（与真实Agent完全解耦）
    
    用途：
    1. 开发和测试Web界面时使用
    2. 不依赖任何实际的LangChain Agent
    3. 提供模拟的响应和数据
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, prompts_path: Optional[str] = None, use_real_agents: bool = False):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.use_real_agents = use_real_agents
        
        self.agents: Dict[str, Any] = {}
        self.sessions: Dict[str, MockAgentSession] = {}
        
        self._mock_questions: List[Dict[str, Any]] = [
            {
                "question": "求极限 $\\lim_{x \\to 0} \\frac{\\sin x}{x}$",
                "metadata": {
                    "question_type": "example",
                    "page": 1,
                    "source": "高等数学",
                    "has_solution": True
                }
            },
            {
                "question": "计算定积分 $\\int_0^1 x^2 dx$",
                "metadata": {
                    "question_type": "exercise",
                    "page": 2,
                    "source": "高等数学",
                    "has_solution": False
                }
            },
            {
                "question": "求导数 $\\frac{d}{dx}(e^{x^2})$",
                "metadata": {
                    "question_type": "example",
                    "page": 3,
                    "source": "高等数学",
                    "has_solution": True
                }
            }
        ]
        
        logger.info("MockAgentManager initialized successfully (agents decoupled)")
    
    def get_agent(self, agent_role: Optional[str] = None) -> Any:
        """
        获取指定类型的Agent（Mock版本）
        """
        role = agent_role or "question_bank"
        return {"role": role, "type": "mock"}
    
    def chat(
        self,
        user_message: str,
        agent_role: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        处理用户聊天请求（Mock版本）
        
        返回模拟的响应，不依赖实际Agent
        """
        try:
            actual_role = agent_role or "question_bank"
            session_id = session_id or f"mock_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            if session_id not in self.sessions:
                self.sessions[session_id] = MockAgentSession(
                    session_id=session_id,
                    agent_role=actual_role
                )
            
            session = self.sessions[session_id]
            
            session.conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            response = self._generate_mock_response(user_message, actual_role)
            
            session.conversation_history.append({
                "role": "assistant",
                "content": response,
                "agent_role": actual_role,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "content": response,
                "agent_role": actual_role,
                "session_id": session_id,
                "metadata": {
                    "conversation_length": len(session.conversation_history),
                    "is_mock": True
                }
            }
            
        except Exception as e:
            logger.error(f"Chat error in MockAgentManager: {e}")
            return {
                "content": f"处理请求时出错：{str(e)}",
                "agent_role": agent_role or "question_bank",
                "error": str(e)
            }
    
    def _generate_mock_response(self, user_message: str, agent_role: str) -> str:
        """
        生成模拟的响应内容
        """
        user_message_lower = user_message.lower()
        
        if "极限" in user_message_lower or "limit" in user_message_lower:
            return (
                "📚 关于极限的概念：\n\n"
                "**极限**是微积分的基础概念，描述函数在某一点附近的行为。\n\n"
                "**定义**：$\\lim_{x \\to a} f(x) = L$ 表示当 $x$ 趋近于 $a$ 时，$f(x)$ 趋近于 $L$。\n\n"
                "**重要的极限公式**：\n"
                "- $\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$\n"
                "- $\\lim_{x \\to \\infty} (1 + \\frac{1}{x})^x = e$\n"
                "- $\\lim_{x \\to 0} \\frac{e^x - 1}{x} = 1$\n\n"
                "有什么具体的极限问题需要我帮助解答吗？"
            )
        
        elif "积分" in user_message_lower or "integral" in user_message_lower:
            return (
                "📚 关于积分的概念：\n\n"
                "**积分**是微积分的两大核心运算之一，分为定积分和不定积分。\n\n"
                "**不定积分**：$\\int f(x) dx = F(x) + C$，其中 $F'(x) = f(x)$\n\n"
                "**定积分**：$\\int_a^b f(x) dx = F(b) - F(a)$\n\n"
                "**基本积分公式**：\n"
                "- $\\int x^n dx = \\frac{x^{n+1}}{n+1} + C \\quad (n \\neq -1)$\n"
                "- $\\int e^x dx = e^x + C$\n"
                "- $\\int \\sin x dx = -\\cos x + C$\n"
                "- $\\int \\cos x dx = \\sin x + C$\n\n"
                "需要我帮你计算具体的积分吗？"
            )
        
        elif "导数" in user_message_lower or "derivative" in user_message_lower:
            return (
                "📚 关于导数的概念：\n\n"
                "**导数**描述函数在某一点的瞬时变化率，是微积分的核心概念。\n\n"
                "**定义**：$f'(a) = \\lim_{h \\to 0} \\frac{f(a+h) - f(a)}{h}$\n\n"
                "**基本导数公式**：\n"
                "- $\\frac{d}{dx}(x^n) = nx^{n-1}$\n"
                "- $\\frac{d}{dx}(e^x) = e^x$\n"
                "- $\\frac{d}{dx}(\\sin x) = \\cos x$\n"
                "- $\\frac{d}{dx}(\\cos x) = -\\sin x$\n"
                "- $\\frac{d}{dx}(\\ln x) = \\frac{1}{x}$\n\n"
                "**链式法则**：$\\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)$\n\n"
                "有什么导数问题需要我帮助解答吗？"
            )
        
        elif "你好" in user_message_lower or "hello" in user_message_lower or "hi" in user_message_lower:
            return (
                "👋 你好！我是数学学习助手。\n\n"
                "我可以帮助你：\n"
                "📖 解释数学概念（极限、导数、积分等）\n"
                "📝 解答数学题目\n"
                "📄 上传PDF或图片进行题目识别\n"
                "🔍 搜索题库中的题目\n\n"
                "有什么我可以帮助你的吗？"
            )
        
        elif "题库" in user_message_lower or "题目" in user_message_lower:
            return (
                "📚 题库管理功能：\n\n"
                "当前题库中有 **3** 道题目（模拟数据）：\n\n"
                "1. 求极限 $\\lim_{x \\to 0} \\frac{\\sin x}{x}$\n"
                "2. 计算定积分 $\\int_0^1 x^2 dx$\n"
                "3. 求导数 $\\frac{d}{dx}(e^{x^2})$\n\n"
                "你可以：\n"
                "- 点击左侧菜单的「题库列表」查看所有题目\n"
                "- 点击「搜索题目」进行语义搜索\n"
                "- 上传PDF或图片添加新题目\n\n"
                "这是Mock模式，不依赖实际的向量数据库。"
            )
        
        else:
            return (
                "🔍 收到你的消息：\n\n"
                f"> {user_message}\n\n"
                "💡 提示（Mock模式）：\n\n"
                "当前运行在 **Mock模式** 下，Web界面已与真实Agent完全解耦。\n\n"
                "你可以测试以下功能：\n"
                "1️⃣ 上传PDF或图片\n"
                "2️⃣ 查看题库列表\n"
                "3️⃣ 搜索题目\n"
                "4️⃣ 输入包含「极限」、「积分」、「导数」的消息查看模拟响应\n\n"
                "要启用真实Agent，请确保LangChain和相关依赖正确安装。"
            )
    
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
        处理PDF文件（Mock版本）
        """
        logger.info(f"Mock PDF processing: {pdf_path} (start={start_page}, end={end_page})")
        
        mock_questions = [
            {
                "question_content": "求函数 $f(x) = x^3 - 3x^2 + 2x$ 的极值",
                "question_type": "example",
                "page": start_page + 1,
                "has_solution": True
            },
            {
                "question_content": "计算 $\\int \\frac{1}{x^2 + 1} dx$",
                "question_type": "exercise",
                "page": start_page + 1,
                "has_solution": False
            }
        ]
        
        self._mock_questions.extend([
            {"question": q["question_content"], "metadata": q} 
            for q in mock_questions
        ])
        
        return {
            "success": True,
            "total_questions": len(mock_questions),
            "extracted_count": len(mock_questions),
            "cross_page_count": 0,
            "example_count": 1,
            "exercise_count": 1,
            "with_solution_count": 1,
            "questions": mock_questions,
            "is_mock": True,
            "message": "PDF处理模拟完成（Mock模式）"
        }
    
    def process_image(
        self,
        image_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理图片文件（Mock版本）
        """
        logger.info(f"Mock image processing: {image_path}")
        
        mock_ocr_text = (
            "题目：求极限\n"
            "lim(x→0) (1 - cos x) / x²\n\n"
            "解答：使用洛必达法则或泰勒展开"
        )
        
        mock_questions = [
            {
                "question_content": "求极限 $\\lim_{x \\to 0} \\frac{1 - \\cos x}{x^2}$",
                "question_type": "example",
                "has_solution": True
            }
        ]
        
        return {
            "success": True,
            "ocr_text": mock_ocr_text,
            "questions": mock_questions,
            "question_count": len(mock_questions),
            "is_mock": True,
            "message": "图片识别模拟完成（Mock模式）"
        }
    
    def get_all_questions(
        self,
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取所有题目（Mock版本）
        """
        if question_type:
            return [
                q for q in self._mock_questions 
                if q.get("metadata", {}).get("question_type") == question_type
            ]
        return self._mock_questions
    
    def search_questions(
        self,
        query: str,
        n_results: int = 5,
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索题目（Mock版本）
        """
        logger.info(f"Mock question search: query='{query}', n_results={n_results}")
        
        results = []
        query_lower = query.lower()
        
        for q in self._mock_questions:
            question_text = q.get("question", "").lower()
            if query_lower in question_text or not query.strip():
                results.append(q)
        
        if question_type:
            results = [
                r for r in results 
                if r.get("metadata", {}).get("question_type") == question_type
            ]
        
        return results[:n_results]
    
    def get_question_stats(self) -> Dict[str, Any]:
        """
        获取题库统计（Mock版本）
        """
        total = len(self._mock_questions)
        examples = sum(
            1 for q in self._mock_questions 
            if q.get("metadata", {}).get("question_type") == "example"
        )
        exercises = total - examples
        
        return {
            "total": total,
            "examples": examples,
            "exercises": exercises,
            "is_mock": True
        }
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的Agent（Mock版本）
        """
        return [
            {
                "role": "question_bank",
                "name": "MockQuestionBankAgent",
                "tools": ["pdf_process", "image_ocr", "question_search"],
                "status": "active",
                "is_mock": True
            },
            {
                "role": "understanding",
                "name": "MockUnderstandingAgent",
                "tools": ["concept_explanation"],
                "status": "active",
                "is_mock": True
            },
            {
                "role": "verification",
                "name": "MockVerificationAgent",
                "tools": ["answer_verification"],
                "status": "active",
                "is_mock": True
            }
        ]
    
    def get_session(self, session_id: str) -> Optional[MockAgentSession]:
        """
        获取会话
        """
        return self.sessions.get(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """
        清除会话
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


def get_agent_manager(use_mock: bool = True) -> Any:
    """
    工厂函数：获取AgentManager实例
    
    Args:
        use_mock: 是否使用Mock版本（默认为True，实现与真实Agent解耦）
    
    Returns:
        AgentManager实例
    """
    if use_mock:
        logger.info("Using MockAgentManager (agents decoupled)")
        return MockAgentManager()
    
    try:
        from src.agents.agent_manager import AgentManager
        logger.info("Using real AgentManager")
        return AgentManager()
    except ImportError as e:
        logger.warning(f"Failed to import real AgentManager: {e}, using MockAgentManager instead")
        return MockAgentManager()
