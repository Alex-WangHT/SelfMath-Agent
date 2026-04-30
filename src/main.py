import os
import sys
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import MathOCRAgent, BaseAgent
from src.prompts import PromptManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_agent(prompts_path: Optional[str] = None) -> MathOCRAgent:
    """
    创建 MathOCRAgent 实例
    
    Args:
        prompts_path: 提示词文件路径
        
    Returns:
        MathOCRAgent 实例
    """
    prompt_manager = PromptManager(prompts_path)
    agent = MathOCRAgent(prompt_manager=prompt_manager)
    return agent


def process_pdf(
    agent: MathOCRAgent,
    pdf_path: str,
    start_page: int = 0,
    end_page: Optional[int] = None,
    enable_cross_page_merge: bool = True
) -> List[Dict[str, Any]]:
    """
    处理 PDF 文件
    
    Args:
        agent: MathOCRAgent 实例
        pdf_path: PDF 文件路径
        start_page: 起始页码
        end_page: 结束页码
        enable_cross_page_merge: 是否启用跨页合并
        
    Returns:
        提取的题目列表
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    questions = agent.process_pdf(
        pdf_path=pdf_path,
        start_page=start_page,
        end_page=end_page,
        enable_cross_page_merge=enable_cross_page_merge
    )
    
    return questions


def search_questions(
    agent: MathOCRAgent,
    query: str,
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """
    搜索题目
    
    Args:
        agent: MathOCRAgent 实例
        query: 搜索查询
        n_results: 返回结果数量
        
    Returns:
        搜索结果列表
    """
    results = agent.search_questions(query, n_results)
    return results


def get_all_questions(agent: MathOCRAgent) -> List[Dict[str, Any]]:
    """
    获取所有题目
    
    Args:
        agent: MathOCRAgent 实例
        
    Returns:
        所有题目列表
    """
    questions = agent.get_all_questions()
    return questions


def run_agent_interaction(agent: MathOCRAgent, user_input: str) -> str:
    """
    运行 Agent 交互
    
    Args:
        agent: MathOCRAgent 实例
        user_input: 用户输入
        
    Returns:
        Agent 响应
    """
    response = agent.run(user_input)
    return response


def main():
    """
    主函数入口
    """
    logger.info("Math OCR Agent System")
    logger.info("=" * 50)
    
    # 创建 Agent 实例
    try:
        agent = create_agent()
        logger.info("MathOCRAgent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MathOCRAgent: {e}")
        sys.exit(1)
    
    # 示例用法
    # 1. 处理 PDF
    # questions = process_pdf(agent, "path/to/file.pdf")
    
    # 2. 搜索题目
    # results = search_questions(agent, "求极限")
    
    # 3. 获取所有题目
    # questions = get_all_questions(agent)
    
    # 4. 直接与 Agent 交互
    # response = run_agent_interaction(agent, "处理 test.pdf 文件")
    
    logger.info("Ready to use. Call the appropriate functions based on your needs.")


if __name__ == "__main__":
    main()
