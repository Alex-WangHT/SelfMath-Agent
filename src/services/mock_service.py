"""
Mock Agent服务实现

这是一个完全与真实Agent解耦的实现，
用于开发、测试和演示Web界面。

不依赖任何外部库（除了标准库），
可以独立运行和测试。
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.interface import (
    AgentResponse,
    AgentInfo,
    Question,
    QuestionStats,
    UploadResult,
    Conversation,
    ChatMessage,
    BaseAgentService,
    QuestionType,
)
from .agent_registry import AgentRegistry, get_registry
from .agent_router import AgentRouter, SimpleKeywordRouter

logger = logging.getLogger(__name__)


class MockAgent:
    """
    Mock Agent实现
    
    模拟Agent的行为，不依赖任何外部库。
    """
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self._response_templates = self._get_response_templates()
    
    def _get_response_templates(self) -> Dict[str, List[str]]:
        """获取响应模板"""
        return {
            "question_bank": [
                "📚 题库管理功能已激活。\n\n我可以帮你：\n- 上传PDF提取题目\n- 上传图片识别题目\n- 搜索题库中的题目\n- 查看题库统计",
                "🗄️ 当前题库中有 3 道题目（模拟数据）：\n\n1. 求极限 $\\lim_{x \\to 0} \\frac{\\sin x}{x}$\n2. 计算定积分 $\\int_0^1 x^2 dx$\n3. 求导数 $\\frac{d}{dx}(e^{x^2})$\n\n上传PDF或图片可以添加更多题目。",
            ],
            "understanding": [
                "📖 概念理解助手已就绪。\n\n请告诉我你想了解什么数学概念？\n例如：极限、导数、积分、级数、微分方程等。",
                "🔍 我可以用简单易懂的方式解释数学概念。\n\n试试问我：\n- 极限是什么？\n- 导数有什么用？\n- 积分和微分的关系是什么？",
            ],
            "verification": [
                "✅ 答案验证助手已就绪。\n\n请把你的解题过程发给我，我来帮你检查是否正确。",
                "🔎 我可以帮你：\n- 验证答案正确性\n- 分析错误原因\n- 提供改进建议\n\n请输入你的题目和解答过程。",
            ],
            "planning": [
                "📋 学习规划助手已就绪。\n\n告诉我你的目标（比如：准备考研数学、复习微积分等），我来帮你制定学习计划。",
            ],
            "assessment": [
                "📊 能力评估助手已就绪。\n\n我可以帮你评估当前的数学水平，找出薄弱环节。\n\n请描述一下你目前的学习情况。",
            ],
        }
    
    def chat(self, user_message: str, **kwargs) -> Dict[str, Any]:
        """模拟聊天响应"""
        message_lower = user_message.lower()
        
        # 关键词匹配的智能响应
        if "极限" in message_lower or "limit" in message_lower:
            return {
                "content": (
                    "📚 关于极限的概念：\n\n"
                    "**极限**是微积分的基础概念，描述函数在某一点附近的行为。\n\n"
                    "**定义**：$\\lim_{x \\to a} f(x) = L$ 表示当 $x$ 趋近于 $a$ 时，$f(x)$ 趋近于 $L$。\n\n"
                    "**重要的极限公式**：\n"
                    "- $\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$\n"
                    "- $\\lim_{x \\to \\infty} (1 + \\frac{1}{x})^x = e$\n"
                    "- $\\lim_{x \\to 0} \\frac{e^x - 1}{x} = 1$\n\n"
                    "有什么具体的极限问题需要我帮助解答吗？"
                )
            }
        
        elif "积分" in message_lower or "integral" in message_lower:
            return {
                "content": (
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
            }
        
        elif "导数" in message_lower or "derivative" in message_lower:
            return {
                "content": (
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
            }
        
        elif "你好" in message_lower or "hello" in message_lower or "hi" in message_lower:
            return {
                "content": (
                    "👋 你好！我是数学学习助手。\n\n"
                    "我可以帮助你：\n"
                    "📖 解释数学概念（极限、导数、积分等）\n"
                    "📝 解答数学题目\n"
                    "📄 上传PDF或图片进行题目识别\n"
                    "🔍 搜索题库中的题目\n\n"
                    "有什么我可以帮助你的吗？"
                )
            }
        
        elif "题库" in message_lower or "题目" in message_lower:
            return {
                "content": (
                    "📚 题库管理功能：\n\n"
                    "当前题库中有 **3** 道题目（模拟数据）：\n\n"
                    "1. 求极限 $\\lim_{x \\to 0} \\frac{\\sin x}{x}$\n"
                    "2. 计算定积分 $\\int_0^1 x^2 dx$\n"
                    "3. 求导数 $\\frac{d}{dx}(e^{x^2})$\n\n"
                    "你可以：\n"
                    "- 点击左侧菜单的「题库列表」查看所有题目\n"
                    "- 点击「搜索题目」进行语义搜索\n"
                    "- 上传PDF或图片添加新题目\n\n"
                    "💡 提示：这是Mock模式，不依赖实际的向量数据库。"
                )
            }
        
        # 默认响应
        templates = self._response_templates.get(self.agent_id, [
            f"🤖 {self.name}已收到你的消息。\n\n这是Mock模式下的响应。"
        ])
        
        response = templates[0] if templates else "收到消息"
        
        return {
            "content": (
                f"🔍 收到你的消息：\n\n"
                f"> {user_message}\n\n"
                f"💡 提示（Mock模式）：\n\n"
                f"当前使用 **{self.name}**。\n\n"
                f"你可以测试以下功能：\n"
                f"1️⃣ 上传PDF或图片\n"
                f"2️⃣ 查看题库列表\n"
                f"3️⃣ 搜索题目\n"
                f"4️⃣ 输入包含「极限」、「积分」、「导数」的消息查看智能响应\n\n"
                f"这是Mock模式，不依赖任何真实的Agent实现。"
            )
        }


class MockAgentService(BaseAgentService):
    """
    Mock Agent服务实现
    
    这是一个完整的Mock实现，
    与真实Agent完全解耦，
    可以独立运行和测试。
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        if self._initialized:
            return
        
        self._initialized = True
        self._registry = registry or get_registry()
        self._router = SimpleKeywordRouter()
        self._conversations: Dict[str, Conversation] = {}
        
        # 模拟题目数据
        self._mock_questions: List[Question] = [
            Question(
                question_id="q001",
                content="求极限 $\\lim_{x \\to 0} \\frac{\\sin x}{x}$",
                question_type=QuestionType.EXAMPLE.value,
                metadata={"page": 1, "source": "高等数学", "has_solution": True}
            ),
            Question(
                question_id="q002",
                content="计算定积分 $\\int_0^1 x^2 dx$",
                question_type=QuestionType.EXERCISE.value,
                metadata={"page": 2, "source": "高等数学", "has_solution": False}
            ),
            Question(
                question_id="q003",
                content="求导数 $\\frac{d}{dx}(e^{x^2})$",
                question_type=QuestionType.EXAMPLE.value,
                metadata={"page": 3, "source": "高等数学", "has_solution": True}
            ),
        ]
        
        # 注册默认的Mock Agent
        self._register_default_agents()
        
        logger.info("MockAgentService initialized (agents decoupled)")
    
    def _register_default_agents(self):
        """注册默认的Mock Agent"""
        agents_config = [
            {
                "agent_id": "question_bank",
                "name": "题库管理Agent",
                "description": "处理PDF上传、OCR识别、题目提取、题库管理",
                "capabilities": ["pdf_process", "image_ocr", "question_search", "question_management"],
                "priority": 100,
            },
            {
                "agent_id": "understanding",
                "name": "概念理解Agent",
                "description": "解释数学概念、原理讲解、公式推导",
                "capabilities": ["concept_explanation", "principle_derivation", "example_walkthrough"],
                "priority": 90,
            },
            {
                "agent_id": "verification",
                "name": "学习验证Agent",
                "description": "验证答案正确性、分析错误原因、提供改进建议",
                "capabilities": ["answer_verification", "error_analysis", "improvement_suggestion"],
                "priority": 80,
            },
            {
                "agent_id": "planning",
                "name": "学习规划Agent",
                "description": "制定个性化学习计划、复习安排",
                "capabilities": ["learning_plan", "review_schedule", "progress_tracking"],
                "priority": 70,
            },
            {
                "agent_id": "assessment",
                "name": "能力评估Agent",
                "description": "评估学习水平、诊断薄弱环节",
                "capabilities": ["level_assessment", "weakness_diagnosis", "recommendation"],
                "priority": 60,
            },
        ]
        
        for config in agents_config:
            agent_id = config["agent_id"]
            mock_agent = MockAgent(
                agent_id=agent_id,
                name=config["name"],
                description=config["description"]
            )
            
            self._registry.register(
                agent_id=agent_id,
                name=config["name"],
                description=config["description"],
                capabilities=config["capabilities"],
                priority=config["priority"],
                factory=lambda a=mock_agent: a
            )
    
    def chat(
        self,
        message: str,
        agent_type: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """处理聊天请求"""
        # 获取或创建对话
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = Conversation(
                conversation_id=conversation_id
            )
        
        conversation = self._conversations[conversation_id]
        
        # 添加用户消息
        conversation.messages.append(
            ChatMessage(role="user", content=message)
        )
        
        # 路由选择Agent
        actual_agent_type = agent_type
        if agent_type == "auto" or not self._registry.is_available(agent_type):
            route_result = self._router.route(
                message=message,
                explicit_agent=agent_type if agent_type != "auto" else None
            )
            actual_agent_type = route_result.agent_id
        
        # 获取Agent实例
        agent = self._registry.get(actual_agent_type)
        
        if agent is None:
            # Fallback
            return AgentResponse(
                content="抱歉，当前服务不可用。这是Mock模式下的默认响应。",
                agent_type=actual_agent_type,
                conversation_id=conversation_id,
                metadata={"error": "Agent unavailable"}
            )
        
        # 调用Agent
        result = agent.chat(message, context=context)
        
        # 添加助手消息
        conversation.messages.append(
            ChatMessage(
                role="assistant",
                content=result.get("content", ""),
                metadata={"agent_type": actual_agent_type}
            )
        )
        
        conversation.updated_at = datetime.now().isoformat()
        
        return AgentResponse(
            content=result.get("content", ""),
            agent_type=actual_agent_type,
            conversation_id=conversation_id,
            metadata=result.get("metadata", {})
        )
    
    def list_agents(self) -> List[AgentInfo]:
        """列出所有可用的Agent"""
        return self._registry.list_agent_info()
    
    def get_agent_capabilities(self, agent_type: str) -> List[str]:
        """获取指定Agent的能力列表"""
        return super().get_agent_capabilities(agent_type)
    
    def process_pdf(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        """处理PDF文件"""
        options = options or {}
        start_page = options.get("start_page", 1)
        
        logger.info(f"Mock PDF processing: {file_path} (start_page={start_page})")
        
        # 模拟提取的题目
        extracted_questions = [
            Question(
                question_id=f"pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}_1",
                content="求函数 $f(x) = x^3 - 3x^2 + 2x$ 的极值",
                question_type=QuestionType.EXAMPLE.value,
                metadata={"page": start_page, "source": Path(file_path).name}
            ),
            Question(
                question_id=f"pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}_2",
                content="计算 $\\int \\frac{1}{x^2 + 1} dx$",
                question_type=QuestionType.EXERCISE.value,
                metadata={"page": start_page, "source": Path(file_path).name}
            ),
        ]
        
        # 添加到模拟题库
        self._mock_questions.extend(extracted_questions)
        
        return UploadResult(
            success=True,
            filename=Path(file_path).name,
            original_filename=Path(file_path).name,
            file_type="pdf",
            questions_extracted=len(extracted_questions),
            questions=extracted_questions,
            metadata={
                "start_page": start_page,
                "end_page": options.get("end_page"),
                "is_mock": True
            }
        )
    
    def process_image(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        """处理图片文件"""
        logger.info(f"Mock image processing: {file_path}")
        
        # 模拟OCR结果
        extracted_questions = [
            Question(
                question_id=f"img_{datetime.now().strftime('%Y%m%d%H%M%S')}_1",
                content="求极限 $\\lim_{x \\to 0} \\frac{1 - \\cos x}{x^2}$",
                question_type=QuestionType.EXAMPLE.value,
                metadata={"source": Path(file_path).name, "has_solution": True}
            ),
        ]
        
        # 添加到模拟题库
        self._mock_questions.extend(extracted_questions)
        
        return UploadResult(
            success=True,
            filename=Path(file_path).name,
            original_filename=Path(file_path).name,
            file_type="image",
            questions_extracted=len(extracted_questions),
            questions=extracted_questions,
            metadata={
                "ocr_text": "题目：求极限\nlim(x→0) (1 - cos x) / x²",
                "is_mock": True
            }
        )
    
    def get_all_questions(
        self,
        question_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Question]:
        """获取所有题目"""
        questions = self._mock_questions
        
        if question_type:
            questions = [
                q for q in questions
                if q.question_type == question_type
            ]
        
        return questions[:limit]
    
    def search_questions(
        self,
        query: str,
        n_results: int = 10,
        question_type: Optional[str] = None
    ) -> List[Question]:
        """搜索题目"""
        logger.info(f"Mock question search: query='{query}'")
        
        results = []
        query_lower = query.lower()
        
        for q in self._mock_questions:
            question_text = q.content.lower()
            if query_lower in question_text or not query.strip():
                results.append(q)
        
        if question_type:
            results = [
                r for r in results
                if r.question_type == question_type
            ]
        
        return results[:n_results]
    
    def get_question_stats(self) -> QuestionStats:
        """获取题库统计"""
        total = len(self._mock_questions)
        examples = sum(
            1 for q in self._mock_questions
            if q.question_type == QuestionType.EXAMPLE.value
        )
        exercises = total - examples
        sources = list(set(
            q.metadata.get("source", "")
            for q in self._mock_questions
            if q.metadata.get("source")
        ))
        
        return QuestionStats(
            total=total,
            examples=examples,
            exercises=exercises,
            sources=sources
        )
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话"""
        return self._conversations.get(conversation_id)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """清除对话"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    def is_agent_available(self, agent_type: str) -> bool:
        """检查Agent是否可用"""
        return self._registry.is_available(agent_type)


def get_mock_service() -> MockAgentService:
    """获取Mock服务单例"""
    return MockAgentService()
