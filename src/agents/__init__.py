"""
Agents 包
使用安全导入，避免在Mock模式下因依赖缺失而失败
"""
import logging

logger = logging.getLogger(__name__)

__all__ = []

try:
    from .mock_agent_manager import MockAgentManager, get_agent_manager
    __all__.extend(["MockAgentManager", "get_agent_manager"])
    logger.info("✓ Successfully imported MockAgentManager")
except ImportError as e:
    logger.warning(f"Failed to import MockAgentManager: {e}")

try:
    from .base_agent import AgentRole
    __all__.append("AgentRole")
    logger.info("✓ Successfully imported AgentRole")
except ImportError as e:
    logger.warning(f"Failed to import AgentRole: {e} (LangChain not available)")

try:
    from .base_agent import BaseAgent
    __all__.append("BaseAgent")
    logger.info("✓ Successfully imported BaseAgent")
except ImportError as e:
    logger.warning(f"Failed to import BaseAgent: {e} (LangChain not available)")

try:
    from .question_bank_agent import QuestionBankManagementAgent
    __all__.append("QuestionBankManagementAgent")
    logger.info("✓ Successfully imported QuestionBankManagementAgent")
except ImportError as e:
    logger.warning(f"Failed to import QuestionBankManagementAgent: {e} (LangChain not available)")

try:
    from .agent_manager import AgentManager
    __all__.append("AgentManager")
    logger.info("✓ Successfully imported AgentManager")
except ImportError as e:
    logger.warning(f"Failed to import AgentManager: {e} (LangChain not available)")

logger.info(f"Agents package ready. Available: {__all__}")
