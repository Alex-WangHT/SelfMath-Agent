"""
Mock Agent 实现

这些是具体的 Agent 实现，用于开发和测试。
桥接器（AgentService）会调用这些具体的 Agent。

设计模式：桥接器模式
- 具体实现层：MockAgent 等
- 抽象层：AgentService（桥接器）
- Web 层只依赖抽象层（桥接器）
"""
import logging
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class MockAgent:
    """
    Mock Agent 实现
    
    模拟真实 Agent 的行为，不依赖任何外部库。
    用于开发、测试和演示 Web 界面。
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        response_templates: Optional[Dict[str, str]] = None
    ):
        """
        初始化 Mock Agent
        
        Args:
            agent_id: Agent 唯一标识
            name: Agent 名称
            description: Agent 描述
            response_templates: 响应模板（可选）
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self._response_templates = response_templates or {}
        
        logger.info(f"MockAgent initialized: {agent_id} ({name})")
    
    def chat(self, user_message: str, **kwargs) -> Dict[str, Any]:
        """
        处理聊天消息
        
        Args:
            user_message: 用户消息
            **kwargs: 额外参数
        
        Returns:
            Dict[str, Any]: 响应内容
        """
        message_lower = user_message.lower()
        
        smart_response = self._get_smart_response(message_lower, user_message)
        if smart_response:
            return {"content": smart_response}
        
        template_response = self._get_template_response(message_lower)
        if template_response:
            return {"content": template_response}
        
        default_response = self._get_default_response(user_message)
        return {"content": default_response}
    
    def _get_smart_response(self, message_lower: str, original_message: str) -> Optional[str]:
        """
        获取智能响应（基于关键词的智能回复）
        
        Args:
            message_lower: 小写的消息
            original_message: 原始消息
        
        Returns:
            Optional[str]: 智能响应，无匹配则返回 None
        """
        if "极限" in message_lower or "limit" in message_lower:
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
        
        if "积分" in message_lower or "integral" in message_lower:
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
        
        if "导数" in message_lower or "derivative" in message_lower:
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
        
        if "你好" in message_lower or "hello" in message_lower or "hi" in message_lower:
            return (
                "👋 你好！我是数学学习助手。\n\n"
                "我可以帮助你：\n"
                "📖 解释数学概念（极限、导数、积分等）\n"
                "📝 解答数学题目\n"
                "📄 上传PDF或图片进行题目识别\n"
                "🔍 搜索题库中的题目\n\n"
                "有什么我可以帮助你的吗？"
            )
        
        if "题库" in message_lower or "题目" in message_lower:
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
                "💡 提示：这是 Mock 模式，不依赖实际的向量数据库。"
            )
        
        return None
    
    def _get_template_response(self, message_lower: str) -> Optional[str]:
        """
        获取模板响应
        
        Args:
            message_lower: 小写的消息
        
        Returns:
            Optional[str]: 模板响应，无匹配则返回 None
        """
        for trigger, response in self._response_templates.items():
            if trigger in message_lower:
                return response
        return None
    
    def _get_default_response(self, user_message: str) -> str:
        """
        获取默认响应
        
        Args:
            user_message: 用户消息
        
        Returns:
            str: 默认响应
        """
        return (
            f"🔍 收到你的消息：\n\n"
            f"> {user_message}\n\n"
            f"💡 提示（Mock 模式）：\n\n"
            f"当前使用 **{self.name}**。\n\n"
            f"你可以测试以下功能：\n"
            f"1️⃣ 上传PDF或图片\n"
            f"2️⃣ 查看题库列表\n"
            f"3️⃣ 搜索题目\n"
            f"4️⃣ 输入包含「极限」、「积分」、「导数」的消息查看智能响应\n\n"
            f"这是 Mock 模式，不依赖任何真实的 Agent 实现。"
        )


def create_mock_agent(
    agent_id: str,
    name: str,
    description: str,
    capabilities: List[str],
    response_templates: Optional[Dict[str, str]] = None
) -> MockAgent:
    """
    创建 Mock Agent 的工厂函数
    
    Args:
        agent_id: Agent 唯一标识
        name: Agent 名称
        description: Agent 描述
        capabilities: 能力列表
        response_templates: 响应模板（可选）
    
    Returns:
        MockAgent: Mock Agent 实例
    """
    return MockAgent(
        agent_id=agent_id,
        name=name,
        description=description,
        response_templates=response_templates
    )
