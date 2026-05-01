import logging

logger = logging.getLogger(__name__)

__all__ = []

try:
    from .prompts import PromptManager
    __all__.append("PromptManager")
    logger.info("Successfully imported PromptManager")
except ImportError as e:
    logger.warning(f"Failed to import PromptManager: {e}")

try:
    from .agents.mock_agent_manager import MockAgentManager, get_agent_manager
    __all__.extend(["MockAgentManager", "get_agent_manager"])
    logger.info("Successfully imported MockAgentManager")
except ImportError as e:
    logger.warning(f"Failed to import MockAgentManager: {e}")

try:
    from .agents.base_agent import AgentRole
    __all__.append("AgentRole")
    logger.info("Successfully imported AgentRole")
except ImportError as e:
    logger.warning(f"Failed to import AgentRole: {e}")

try:
    from .agents.base_agent import BaseAgent
    __all__.append("BaseAgent")
    logger.info("Successfully imported BaseAgent")
except ImportError as e:
    logger.warning(f"Failed to import BaseAgent: {e}")

try:
    from .agents.question_bank_agent import QuestionBankManagementAgent
    __all__.append("QuestionBankManagementAgent")
    logger.info("Successfully imported QuestionBankManagementAgent")
except ImportError as e:
    logger.warning(f"Failed to import QuestionBankManagementAgent: {e}")

try:
    from .agents.agent_manager import AgentManager
    __all__.append("AgentManager")
    logger.info("Successfully imported AgentManager")
except ImportError as e:
    logger.warning(f"Failed to import AgentManager: {e}")

logger.info(f"Available exports: {__all__}")
