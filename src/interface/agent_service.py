"""
Agent服务桥接器

这是 Web 层和具体 Agent 实现之间的核心桥梁。
提供统一的调用入口，内部调用具体的 Agent 实现。

设计模式：桥接器模式 (Bridge Pattern)
- Web 层只依赖这个桥接器
- 桥接器内部调用具体的 Agent 实现
- 可以通过配置切换 Mock/Real Agent
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .data_models import (
    AgentResponse,
    AgentInfo,
    Question,
    QuestionStats,
    QuestionType,
    UploadResult,
    Conversation,
    ChatMessage,
)
from .agent_registry import AgentRegistry, get_registry
from .agent_router import AgentRouter, SimpleKeywordRouter


logger = logging.getLogger(__name__)


class AgentService:
    """
    Agent服务桥接器
    
    作为 Web 层和具体 Agent 实现之间的桥梁。
    提供统一的 API 接口，内部调用具体的 Agent 实现。
    
    使用方式：
    ```python
    from src.interface import AgentService, get_service
    
    # 获取服务单例
    service = get_service()
    
    # 或创建自定义服务
    service = AgentService(use_mock=True)
    service.init_mock_agents()
    
    # 调用 API
    response = service.chat(
        message="你好",
        agent_type="question_bank",
        conversation_id="conv1"
    )
    ```
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        use_mock: bool = True,
        registry: Optional[AgentRegistry] = None,
        router: Optional[AgentRouter] = None
    ):
        """
        初始化 Agent 服务桥接器
        
        Args:
            use_mock: 是否使用 Mock Agent
            registry: 自定义注册中心（可选）
            router: 自定义路由器（可选）
        """
        if self._initialized:
            return
        
        self._initialized = True
        self._use_mock = use_mock
        self._registry = registry or get_registry()
        self._router = router or SimpleKeywordRouter()
        
        self._conversations: Dict[str, Conversation] = {}
        self._mock_questions: List[Question] = []
        
        if use_mock:
            self._init_mock_data()
        
        logger.info(f"AgentService initialized (use_mock={use_mock})")
    
    def _init_mock_data(self):
        """初始化 Mock 数据"""
        self._mock_questions = [
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
        logger.info("Mock questions initialized")
    
    def register_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: List[str],
        factory: Any
    ):
        """
        注册一个 Agent（通用方法）
        
        Args:
            agent_id: Agent 唯一标识
            name: Agent 名称
            description: Agent 描述
            capabilities: 能力列表
            factory: 工厂函数或实例
        """
        self._registry.register(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=capabilities,
            factory=factory if callable(factory) else lambda: factory
        )
        
        logger.info(f"Agent registered: {agent_id} ({name})")
    
    def register_mock_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: List[str],
        response_templates: Optional[Dict[str, str]] = None
    ):
        """
        注册一个 Mock Agent
        
        Args:
            agent_id: Agent 唯一标识
            name: Agent 名称
            description: Agent 描述
            capabilities: 能力列表
            response_templates: 响应模板（可选）
        """
        from src.agents.mock_agents import MockAgent
        
        mock_agent = MockAgent(
            agent_id=agent_id,
            name=name,
            description=description,
            response_templates=response_templates
        )
        
        self._registry.register(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=capabilities,
            factory=lambda: mock_agent
        )
        
        logger.info(f"Mock Agent registered: {agent_id} ({name})")
    
    def init_mock_agents(self):
        """
        初始化默认的 Mock Agents
        
        这是一个便捷方法，注册所有默认的 Mock Agent。
        """
        default_agents = [
            {
                "agent_id": "question_bank",
                "name": "题库管理助手",
                "description": "处理PDF上传、OCR识别、题目提取、题库管理",
                "capabilities": ["pdf_process", "image_ocr", "question_search", "question_management"],
            },
            {
                "agent_id": "understanding",
                "name": "概念理解助手",
                "description": "解释数学概念、原理讲解、公式推导",
                "capabilities": ["concept_explanation", "principle_derivation", "example_walkthrough"],
            },
            {
                "agent_id": "verification",
                "name": "学习验证助手",
                "description": "验证答案正确性、分析错误原因、提供改进建议",
                "capabilities": ["answer_verification", "error_analysis", "improvement_suggestion"],
            },
            {
                "agent_id": "planning",
                "name": "学习规划助手",
                "description": "制定个性化学习计划、复习安排",
                "capabilities": ["learning_plan", "review_schedule", "progress_tracking"],
            },
            {
                "agent_id": "assessment",
                "name": "能力评估助手",
                "description": "评估学习水平、诊断薄弱环节",
                "capabilities": ["level_assessment", "weakness_diagnosis", "recommendation"],
            },
        ]
        
        for agent_config in default_agents:
            self.register_mock_agent(**agent_config)
        
        logger.info("All default Mock Agents initialized")
    
    # ========== 核心 API ==========
    
    def chat(
        self,
        message: str,
        agent_type: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        处理聊天请求
        
        这是核心的桥接方法：
        1. 获取或创建对话
        2. 路由选择合适的 Agent
        3. 调用具体的 Agent 实例
        4. 返回统一格式的响应
        
        Args:
            message: 用户消息内容
            agent_type: 指定的 Agent 类型，或 "auto" 自动选择
            conversation_id: 对话 ID
            context: 上下文信息
        
        Returns:
            AgentResponse: 统一格式的响应
        """
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = Conversation(
                conversation_id=conversation_id
            )
        
        conversation = self._conversations[conversation_id]
        conversation.messages.append(
            ChatMessage(role="user", content=message)
        )
        
        actual_agent_type = agent_type
        if agent_type == "auto" or not self._registry.is_available(agent_type):
            route_result = self._router.route(
                message=message,
                explicit_agent=agent_type if agent_type != "auto" else None
            )
            actual_agent_type = route_result.agent_id
            logger.info(f"Auto-routed to: {actual_agent_type}")
        
        agent = self._registry.get(actual_agent_type)
        
        if agent is None:
            response_content = (
                f"抱歉，当前服务不可用。\n\n"
                f"请求的 Agent: {actual_agent_type}\n"
                f"这是 Mock 模式下的默认响应。"
            )
            conversation.messages.append(
                ChatMessage(
                    role="assistant",
                    content=response_content,
                    metadata={"agent_type": actual_agent_type, "error": "Agent unavailable"}
                )
            )
            return AgentResponse(
                content=response_content,
                agent_type=actual_agent_type,
                conversation_id=conversation_id,
                metadata={"error": "Agent unavailable"}
            )
        
        try:
            result = agent.chat(message, context=context)
        except Exception as e:
            logger.error(f"Agent chat error: {e}")
            result = {
                "content": f"抱歉，处理消息时出现错误：{str(e)}",
                "metadata": {"error": str(e)}
            }
        
        response_content = result.get("content", "抱歉，没有收到响应。")
        response_metadata = result.get("metadata", {})
        
        conversation.messages.append(
            ChatMessage(
                role="assistant",
                content=response_content,
                metadata={"agent_type": actual_agent_type, **response_metadata}
            )
        )
        conversation.updated_at = datetime.now().isoformat()
        
        return AgentResponse(
            content=response_content,
            agent_type=actual_agent_type,
            conversation_id=conversation_id,
            metadata=response_metadata
        )
    
    def list_agents(self) -> List[AgentInfo]:
        """列出所有可用的 Agent"""
        return self._registry.list_agent_info()
    
    def get_agent_capabilities(self, agent_type: str) -> List[str]:
        """获取指定 Agent 的能力列表"""
        agents = self.list_agents()
        for agent in agents:
            if agent.agent_id == agent_type:
                return agent.capabilities
        return []
    
    def is_agent_available(self, agent_type: str) -> bool:
        """检查 Agent 是否可用"""
        return self._registry.is_available(agent_type)
    
    # ========== 题库相关 API ==========
    
    def process_pdf(
        self,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        """
        处理 PDF 文件
        
        Args:
            file_path: 文件路径
            options: 处理选项
        
        Returns:
            UploadResult: 上传结果
        """
        options = options or {}
        start_page = options.get("start_page", 1)
        
        logger.info(f"Processing PDF: {file_path} (start_page={start_page})")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        extracted_questions = [
            Question(
                question_id=f"pdf_{timestamp}_1",
                content="求函数 $f(x) = x^3 - 3x^2 + 2x$ 的极值",
                question_type=QuestionType.EXAMPLE.value,
                metadata={"page": start_page, "source": Path(file_path).name}
            ),
            Question(
                question_id=f"pdf_{timestamp}_2",
                content="计算 $\\int \\frac{1}{x^2 + 1} dx$",
                question_type=QuestionType.EXERCISE.value,
                metadata={"page": start_page, "source": Path(file_path).name}
            ),
        ]
        
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
        """
        处理图片文件
        
        Args:
            file_path: 文件路径
            options: 处理选项
        
        Returns:
            UploadResult: 上传结果
        """
        logger.info(f"Processing image: {file_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        extracted_questions = [
            Question(
                question_id=f"img_{timestamp}_1",
                content="求极限 $\\lim_{x \\to 0} \\frac{1 - \\cos x}{x^2}$",
                question_type=QuestionType.EXAMPLE.value,
                metadata={"source": Path(file_path).name, "has_solution": True}
            ),
        ]
        
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
        """
        获取所有题目
        
        Args:
            question_type: 题目类型过滤（example/exercise）
            limit: 返回数量限制
        
        Returns:
            List[Question]: 题目列表
        """
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
        """
        搜索题目
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            question_type: 题目类型过滤
        
        Returns:
            List[Question]: 搜索结果
        """
        logger.info(f"Searching questions: query='{query}'")
        
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
        """
        获取题库统计
        
        Returns:
            QuestionStats: 统计信息
        """
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
    
    # ========== 对话相关 API ==========
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话"""
        return self._conversations.get(conversation_id)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """清除对话"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info(f"Conversation cleared: {conversation_id}")
            return True
        return False
    
    # ========== 配置方法 ==========
    
    def set_mock_mode(self, enabled: bool):
        """
        设置 Mock 模式
        
        Args:
            enabled: 是否启用 Mock 模式
        """
        self._use_mock = enabled
        logger.info(f"Mock mode set to: {enabled}")
    
    def get_registry(self) -> AgentRegistry:
        """获取注册中心"""
        return self._registry
    
    def get_router(self) -> AgentRouter:
        """获取路由器"""
        return self._router


def get_service(use_mock: bool = True) -> AgentService:
    """
    获取 Agent 服务单例
    
    Args:
        use_mock: 是否使用 Mock Agent
    
    Returns:
        AgentService: 服务实例
    """
    service = AgentService(use_mock=use_mock)
    if use_mock and not service._registry.list_agents():
        service.init_mock_agents()
    return service
