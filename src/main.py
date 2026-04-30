import os
import sys
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import QuestionBankManagementAgent, BaseAgent
from src.prompts import PromptManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_question_bank_agent(prompts_path: Optional[str] = None) -> QuestionBankManagementAgent:
    """
    创建题库管理 Agent 实例
    
    Args:
        prompts_path: 提示词文件路径
        
    Returns:
        QuestionBankManagementAgent 实例
    """
    prompt_manager = PromptManager(prompts_path)
    agent = QuestionBankManagementAgent(prompt_manager=prompt_manager)
    return agent


def process_pdf(
    agent: QuestionBankManagementAgent,
    pdf_path: str,
    start_page: int = 0,
    end_page: Optional[int] = None,
    enable_cross_page_merge: bool = True,
    auto_save: bool = True
) -> List[Dict[str, Any]]:
    """
    处理 PDF 文件，提取题目（含解法）
    
    Args:
        agent: QuestionBankManagementAgent 实例
        pdf_path: PDF 文件路径
        start_page: 起始页码
        end_page: 结束页码
        enable_cross_page_merge: 是否启用跨页合并
        auto_save: 是否自动保存到题库
        
    Returns:
        提取的题目列表
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    questions = agent.process_pdf(
        pdf_path=pdf_path,
        start_page=start_page,
        end_page=end_page,
        enable_cross_page_merge=enable_cross_page_merge,
        auto_save=auto_save
    )
    
    return questions


def add_question(
    agent: QuestionBankManagementAgent,
    question_number: str,
    question_type: str,
    question_content: str,
    answer_content: str = "",
    solution_content: str = "",
    source: str = ""
) -> str:
    """
    添加单道题目到题库
    
    【重要】每道题都必须有解法标识（solution_content）
    
    Args:
        agent: QuestionBankManagementAgent 实例
        question_number: 题号
        question_type: 题目类型（example/exercise）
        question_content: 题目内容
        answer_content: 答案内容
        solution_content: 解法内容（解题步骤、推导过程等）
        source: 来源
        
    Returns:
        题目 ID
    """
    return agent.add_question(
        question_number=question_number,
        question_type=question_type,
        question_content=question_content,
        answer_content=answer_content,
        solution_content=solution_content,
        source=source
    )


def batch_add_questions(
    agent: QuestionBankManagementAgent,
    questions: List[Dict[str, Any]],
    source: str = ""
) -> List[str]:
    """
    批量添加题目到题库
    
    Args:
        agent: QuestionBankManagementAgent 实例
        questions: 题目列表，每道题必须包含 solution_content
        source: 来源
        
    Returns:
        题目 ID 列表
    """
    return agent.batch_add_questions(questions, source)


def search_questions(
    agent: QuestionBankManagementAgent,
    query: str,
    n_results: int = 5,
    question_type: str = None
) -> List[Dict[str, Any]]:
    """
    搜索题目
    
    Args:
        agent: QuestionBankManagementAgent 实例
        query: 搜索查询
        n_results: 返回结果数量
        question_type: 题目类型过滤（example/exercise）
        
    Returns:
        搜索结果列表
    """
    results = agent.search_questions(query, n_results, question_type)
    return results


def get_all_questions(
    agent: QuestionBankManagementAgent,
    question_type: str = None
) -> List[Dict[str, Any]]:
    """
    获取所有题目
    
    Args:
        agent: QuestionBankManagementAgent 实例
        question_type: 题目类型过滤（example/exercise）
        
    Returns:
        所有题目列表
    """
    questions = agent.get_all_questions(question_type)
    return questions


def get_question_stats(agent: QuestionBankManagementAgent) -> Dict[str, Any]:
    """
    获取题库统计信息
    
    Args:
        agent: QuestionBankManagementAgent 实例
        
    Returns:
        统计信息
    """
    return agent.get_stats()


def run_agent_interaction(agent: QuestionBankManagementAgent, user_input: str) -> str:
    """
    运行 Agent 交互
    
    Args:
        agent: QuestionBankManagementAgent 实例
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
    logger.info("题库管理 Agent 系统")
    logger.info("=" * 50)
    
    try:
        agent = create_question_bank_agent()
        logger.info("题库管理 Agent 初始化成功")
        
        stats = get_question_stats(agent)
        logger.info(f"题库统计: 总题数={stats.get('total_questions', 0)}, "
                   f"例题={stats.get('example_count', 0)}, "
                   f"习题={stats.get('exercise_count', 0)}, "
                   f"有解法={stats.get('with_solution_count', 0)}")
                   
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        sys.exit(1)
    
    logger.info("=" * 50)
    logger.info("可用功能:")
    logger.info("1. process_pdf: 处理 PDF，提取题目和答案")
    logger.info("2. add_question: 手动添加题目到题库")
    logger.info("3. batch_add_questions: 批量添加题目")
    logger.info("4. search_questions: 搜索题目")
    logger.info("5. get_all_questions: 获取所有题目")
    logger.info("6. get_question_stats: 获取题库统计")
    logger.info("7. run_agent_interaction: 直接与 Agent 对话")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
