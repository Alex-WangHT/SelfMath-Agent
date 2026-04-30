import os
import base64
import json
import fitz
import chromadb
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from chromadb.utils import embedding_functions
from langchain_core.tools import tool

from .base_agent import BaseAgent
from src.prompts import PromptManager

logger = logging.getLogger(__name__)


class QuestionBankManagementAgent(BaseAgent):
    """
    题库管理 Agent，用于习题集的完整录入和管理
    继承自 BaseAgent 基类，实现以下核心功能：
    1. OCR 识别：识别 PDF/图片中的数学题目
    2. 解法 OCR：对每道例题和习题都打上解法标识
    3. 题库管理：题目录入、分类、更新、删除
    4. 分类管理：例题(example)和习题(exercise)的完整识别
    """
    
    def __init__(
        self,
        prompt_manager: Optional[PromptManager] = None,
        prompts_path: Optional[str] = None
    ):
        """
        初始化题库管理 Agent
        
        Args:
            prompt_manager: 提示词管理器
            prompts_path: 提示词文件路径
        """
        self.db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        self.collection_name = os.getenv("CHROMA_COLLECTION", "math_questions")
        
        self.temp_dir = Path("./data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.db = None
        self.collection = None
        
        self.question_stats = {
            "total_questions": 0,
            "example_count": 0,
            "exercise_count": 0,
            "with_solution_count": 0
        }
        
        super().__init__(
            prompt_manager=prompt_manager,
            prompts_path=prompts_path,
            agent_name="QuestionBankManagementAgent"
        )
    
    def _create_tools(self) -> List:
        """
        创建题库管理 Agent 的工具列表
        
        Returns:
            工具列表
        """
        tools = [
            self._pdf_to_images_tool,
            self._ocr_image_with_solution_tool,
            self._parse_questions_with_solution_tool,
            self._merge_cross_page_questions_tool,
            self._add_question_to_bank_tool,
            self._batch_add_questions_tool,
            self._update_question_tool,
            self._delete_question_tool,
            self._search_questions_tool,
            self._get_question_by_number_tool,
            self._get_all_questions_tool,
            self._get_question_stats_tool,
            self._categorize_questions_tool,
            self._analyze_solution_tool
        ]
        
        return tools
    
    def _get_system_prompt(self) -> str:
        """
        获取题库管理 Agent 的系统提示词
        
        Returns:
            系统提示词字符串
        """
        system_prompt = self.prompt_manager.get_prompt("question_bank_agent", "system_prompt")
        
        if not system_prompt:
            system_prompt = """你是一个专业的题库管理 Agent，负责数学习题集的完整录入和管理。

你的核心职责：
1. OCR 识别：从 PDF 或图片中识别数学题目
2. 解法 OCR：对每道例题和习题都完整识别题目内容和解法内容
3. 题库管理：题目录入、更新、删除、搜索
4. 分类管理：区分例题(example)和习题(exercise)

你可以使用以下工具：
1. pdf_to_images: 将 PDF 文件转换为图片
2. ocr_image_with_solution: 对图片进行 OCR 识别，完整识别题目和解法
3. parse_questions_with_solution: 解析 OCR 结果，提取题目、分类、解法
4. merge_cross_page_questions: 合并跨页的数学题目
5. add_question_to_bank: 将单道题目录入题库
6. batch_add_questions: 批量录入题目到题库
7. update_question: 更新题库中的题目
8. delete_question: 从题库中删除题目
9. search_questions: 在题库中搜索题目
10. get_question_by_number: 按题号查询题目
11. get_all_questions: 获取题库中的所有题目
12. get_question_stats: 获取题库统计信息
13. categorize_questions: 对题目进行分类
14. analyze_solution: 分析题目的解法

【重要的分类规则】
- 例题(example)：题号以"例"字开头，如"例1.1"、"例2.3.1"等
  - 必须完整提取：题目内容 + 答案内容 + 解法内容
  - 解法内容包括：解题步骤、推导过程、证明过程等
  - 必须打上解法标识：solution_content 字段

- 习题(exercise)：题号以纯数字开头，如"1.1.1"、"2.3.4"等
  - 必须完整提取：题目内容 + 解法内容（如果有）
  - 即使习题没有答案，也要识别可能的解法提示或思路
  - 必须打上解法标识：solution_content 字段

【解法 OCR 规则】
1. 解法起始标识："【答案】"、"解："、"证明："、"分析："、"解答："、"答案："、"【解】"、"【证明】"
2. 解法内容包括：
   - 解题步骤和推导过程
   - 证明过程
   - 计算过程
   - 思路分析
   - 答案或结论
3. 每道题（例题和习题）都必须有 solution_content 字段
4. 如果没有识别到解法，solution_content 设为空字符串""

请根据用户的需求，智能地选择和调用工具。"""
        
        return system_prompt
    
    def _init_chroma(self):
        """初始化 ChromaDB 连接"""
        if self.collection is None:
            self.db = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.db.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
            logger.info(f"ChromaDB initialized at {self.db_path}")
            self._refresh_stats()
    
    def _refresh_stats(self):
        """刷新题库统计信息"""
        self._init_chroma()
        results = self.collection.get()
        
        total = len(results["ids"])
        examples = 0
        exercises = 0
        with_solution = 0
        
        for metadata in results["metadatas"]:
            q_type = metadata.get("question_type", "exercise")
            if q_type == "example":
                examples += 1
            else:
                exercises += 1
            
            solution = metadata.get("solution_content", "")
            if solution:
                with_solution += 1
        
        self.question_stats = {
            "total_questions": total,
            "example_count": examples,
            "exercise_count": exercises,
            "with_solution_count": with_solution
        }
    
    @tool
    def _pdf_to_images_tool(
        self,
        pdf_path: str,
        start_page: int = 0,
        end_page: Optional[int] = None
    ) -> List[str]:
        """
        将 PDF 文件转换为图片
        
        Args:
            pdf_path: PDF 文件路径
            start_page: 起始页码（0-based）
            end_page: 结束页码（exclusive），如果为 None 则转换到最后一页
            
        Returns:
            转换后的图片路径列表
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        if end_page is None:
            end_page = total_pages
        
        start_page = max(0, start_page)
        end_page = min(total_pages, end_page)
        
        image_paths = []
        pdf_name = Path(pdf_path).stem
        
        for page_num in range(start_page, end_page):
            page = doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            
            image_path = self.temp_dir / f"{pdf_name}_page_{page_num + 1}.png"
            pix.save(str(image_path))
            image_paths.append(str(image_path))
            
            logger.info(f"Processed page {page_num + 1}/{total_pages}")
        
        doc.close()
        return image_paths
    
    @tool
    def _ocr_image_with_solution_tool(self, image_path: str) -> str:
        """
        对图片进行 OCR 识别，完整识别题目和解法
        
        【重要】此方法会完整识别：
        1. 题目内容
        2. 答案内容
        3. 解法内容（解题步骤、推导过程、证明过程等）
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            OCR 识别结果文本（包含题目、答案、解法）
        """
        base64_img = self._encode_image(image_path)
        
        system_prompt = self.prompt_manager.get_prompt_or_raise("ocr_image_with_solution", "system_prompt")
        user_text = self.prompt_manager.get_prompt("ocr_image_with_solution", "user_text") or "识别这张图片中的数学内容，包括题目、答案和解法。"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                ]
            }
        ]
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": 8192,
                "temperature": 0.0
            },
            timeout=180
        )
        
        if response.status_code != 200:
            raise Exception(f"OCR API failed: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    @tool
    def _parse_questions_with_solution_tool(self, ocr_text: str) -> List[Dict[str, Any]]:
        """
        解析 OCR 结果，提取题目、分类、解法
        
        【核心功能】
        1. 分类识别：区分例题(example)和习题(exercise)
        2. 题目提取：提取完整的题目内容
        3. 答案提取：提取答案内容
        4. 解法提取：提取解法内容（解题步骤、推导过程等）
        
        【输出字段说明】
        - question_number: 题号
        - question_type: 题目类型（example/exercise）
        - question_content: 题目内容
        - answer_content: 答案内容
        - solution_content: 解法内容（必须字段，每道题都要有）
        - raw_text: 原始文本
        - is_incomplete: 是否不完整
        - page_hint: 页码提示
        
        Args:
            ocr_text: OCR 识别结果文本
            
        Returns:
            解析后的题目列表，每道题都包含解法标识
        """
        system_prompt = self.prompt_manager.get_prompt_or_raise("parse_questions_with_solution", "system_prompt")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"解析以下内容，提取题目、答案和解法：\n{ocr_text}"}
        ]
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": 8192,
                "temperature": 0.0
            },
            timeout=180
        )
        
        if response.status_code != 200:
            raise Exception(f"Parse API failed: {response.status_code} - {response.text}")
        
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        
        try:
            json_str = self._extract_json(text)
            questions = json.loads(json_str)
            
            for q in questions:
                q_num = q.get("question_number", "")
                
                if q_num.startswith("例"):
                    q["question_type"] = "example"
                elif q_num and (q_num[0].isdigit() or (len(q_num) > 1 and q_num[1].isdigit())):
                    q["question_type"] = "exercise"
                
                q.setdefault("solution_content", "")
                q.setdefault("answer_content", "")
                q.setdefault("raw_text", ocr_text)
                q.setdefault("is_incomplete", False)
            
            return questions
        except json.JSONDecodeError as e:
            logger.error(f"Parse failed: {e}, text: {text[:500]}")
            return []
    
    def _extract_json(self, text: str, prefer_object: bool = False) -> str:
        """从文本中提取 JSON"""
        if prefer_object:
            start = text.find('{')
            if start == -1:
                start = text.find('[')
        else:
            start = text.find('[')
            if start == -1:
                start = text.find('{')
        
        if start == -1:
            return text
        
        balance = 0
        in_string = False
        escape = False
        result = []
        
        for char in text[start:]:
            if escape:
                escape = False
                result.append(char)
                continue
            if char == '\\':
                escape = True
                result.append(char)
                continue
            if char == '"':
                in_string = not in_string
            if not in_string:
                if char in '{[':
                    balance += 1
                elif char in '}]':
                    balance -= 1
            result.append(char)
            if not in_string and balance == 0:
                break
        
        return ''.join(result)
    
    @tool
    def _merge_cross_page_questions_tool(
        self,
        page_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并跨页的数学题目
        
        Args:
            page_results: 每页的解析结果列表
            
        Returns:
            合并后的题目列表
        """
        if not page_results:
            return []
        
        merged_questions = []
        pending_question = None
        
        for page_info in page_results:
            page_num = page_info["page_num"]
            questions = page_info.get("questions", [])
            
            for q in questions:
                is_incomplete = q.get("is_incomplete", False)
                
                if pending_question is not None:
                    if self._is_potential_question_start(q.get("raw_text", "")[:50]):
                        pending_question["is_incomplete"] = False
                        if "pages" not in pending_question:
                            pending_question["pages"] = [pending_question.get("page_num", 0)]
                        merged_questions.append(pending_question)
                        pending_question = None
                    else:
                        pending_question["question_content"] = (
                            pending_question.get("question_content", "") + 
                            "\n" + q.get("question_content", "")
                        )
                        pending_question["answer_content"] = (
                            pending_question.get("answer_content", "") + 
                            "\n" + q.get("answer_content", "")
                        )
                        pending_question["solution_content"] = (
                            pending_question.get("solution_content", "") + 
                            "\n" + q.get("solution_content", "")
                        )
                        pending_question["raw_text"] = (
                            pending_question.get("raw_text", "") + 
                            "\n" + q.get("raw_text", "")
                        )
                        pending_question["pages"] = pending_question.get("pages", []) + [page_num]
                        pending_question["is_incomplete"] = is_incomplete
                        
                        if not is_incomplete:
                            merged_questions.append(pending_question)
                            pending_question = None
                        continue
                
                if is_incomplete:
                    pending_question = q.copy()
                    pending_question["page_num"] = page_num
                    pending_question["pages"] = [page_num]
                else:
                    q["pages"] = [page_num]
                    merged_questions.append(q)
        
        if pending_question is not None:
            pending_question["is_incomplete"] = False
            merged_questions.append(pending_question)
        
        return merged_questions
    
    def _is_potential_question_start(self, text: str) -> bool:
        """检查文本是否可能是新题目的开始"""
        import re
        
        if re.match(r'^\s*例\d+', text):
            return True
        
        if re.match(r'^\s*\d+\.\d+\.\d+', text):
            return True
        
        return False
    
    @tool
    def _add_question_to_bank_tool(
        self,
        question_number: str,
        question_type: str,
        question_content: str,
        answer_content: str = "",
        solution_content: str = "",
        raw_text: str = "",
        source: str = "",
        pages: List[int] = None
    ) -> str:
        """
        将单道题目录入题库
        
        【必填字段】
        - question_number: 题号
        - question_type: 题目类型（example/exercise）
        - question_content: 题目内容
        
        【重要字段】
        - solution_content: 解法内容（必须填写，每道题都要有解法标识）
        - answer_content: 答案内容
        
        Args:
            question_number: 题号
            question_type: 题目类型（example/exercise）
            question_content: 题目内容
            answer_content: 答案内容
            solution_content: 解法内容（解题步骤、推导过程等）
            raw_text: 原始文本
            source: 来源标识
            pages: 页码列表
            
        Returns:
            录入的题目 ID
        """
        self._init_chroma()
        
        question_data = {
            "question_number": question_number,
            "question_type": question_type,
            "question_content": question_content,
            "answer_content": answer_content or "",
            "solution_content": solution_content or "",
            "raw_text": raw_text or "",
            "source": source or "",
            "pages": json.dumps(pages or []),
            "page_count": len(pages) if pages else 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        qid = f"q_{source}_{hash(question_content)}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        content_parts = [question_content]
        if answer_content:
            content_parts.append(f"\n【答案】{answer_content}")
        if solution_content:
            content_parts.append(f"\n【解法】{solution_content}")
        
        document = "\n".join(content_parts)
        
        self.collection.add(
            ids=[qid],
            documents=[document],
            metadatas=[question_data]
        )
        
        logger.info(f"Added question {question_number} to bank")
        self._refresh_stats()
        
        return qid
    
    @tool
    def _batch_add_questions_tool(
        self,
        questions: List[Dict[str, Any]],
        source: str = ""
    ) -> List[str]:
        """
        批量录入题目到题库
        
        【每道题的必要字段】
        - question_number: 题号
        - question_type: 题目类型（example/exercise）
        - question_content: 题目内容
        - solution_content: 解法内容（必须有）
        
        Args:
            questions: 题目列表
            source: 来源标识
            
        Returns:
            录入的题目 ID 列表
        """
        self._init_chroma()
        
        if not questions:
            return []
        
        ids = []
        documents = []
        metadatas = []
        
        for i, q in enumerate(questions):
            qid = f"q_{source}_{hash(q.get('question_content', ''))}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
            ids.append(qid)
            
            content_parts = [q.get("question_content", "")]
            answer = q.get("answer_content", "")
            if answer:
                content_parts.append(f"\n【答案】{answer}")
            solution = q.get("solution_content", "")
            if solution:
                content_parts.append(f"\n【解法】{solution}")
            documents.append("\n".join(content_parts))
            
            metadatas.append({
                "question_number": q.get("question_number", ""),
                "question_type": q.get("question_type", "exercise"),
                "question_content": q.get("question_content", ""),
                "answer_content": q.get("answer_content", ""),
                "solution_content": q.get("solution_content", ""),
                "raw_text": q.get("raw_text", ""),
                "source": source,
                "pages": json.dumps(q.get("pages", [])),
                "page_count": len(q.get("pages", [])) or 1,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Batch added {len(questions)} questions to bank")
        self._refresh_stats()
        
        return ids
    
    @tool
    def _update_question_tool(
        self,
        question_id: str,
        question_number: str = None,
        question_type: str = None,
        question_content: str = None,
        answer_content: str = None,
        solution_content: str = None
    ) -> bool:
        """
        更新题库中的题目
        
        Args:
            question_id: 题目 ID
            question_number: 新的题号（可选）
            question_type: 新的题目类型（可选）
            question_content: 新的题目内容（可选）
            answer_content: 新的答案内容（可选）
            solution_content: 新的解法内容（可选）
            
        Returns:
            是否更新成功
        """
        self._init_chroma()
        
        try:
            results = self.collection.get(ids=[question_id])
            
            if not results["ids"]:
                logger.warning(f"Question not found: {question_id}")
                return False
            
            existing_metadata = results["metadatas"][0]
            existing_document = results["documents"][0] if results["documents"] else ""
            
            updates = {}
            if question_number is not None:
                updates["question_number"] = question_number
            if question_type is not None:
                updates["question_type"] = question_type
            if question_content is not None:
                updates["question_content"] = question_content
            if answer_content is not None:
                updates["answer_content"] = answer_content
            if solution_content is not None:
                updates["solution_content"] = solution_content
            
            updates["updated_at"] = datetime.now().isoformat()
            
            new_metadata = {**existing_metadata, **updates}
            
            new_content_parts = [new_metadata.get("question_content", "")]
            answer = new_metadata.get("answer_content", "")
            if answer:
                new_content_parts.append(f"\n【答案】{answer}")
            solution = new_metadata.get("solution_content", "")
            if solution:
                new_content_parts.append(f"\n【解法】{solution}")
            new_document = "\n".join(new_content_parts)
            
            self.collection.update(
                ids=[question_id],
                documents=[new_document],
                metadatas=[new_metadata]
            )
            
            logger.info(f"Updated question: {question_id}")
            self._refresh_stats()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update question: {e}")
            return False
    
    @tool
    def _delete_question_tool(self, question_id: str) -> bool:
        """
        从题库中删除题目
        
        Args:
            question_id: 题目 ID
            
        Returns:
            是否删除成功
        """
        self._init_chroma()
        
        try:
            self.collection.delete(ids=[question_id])
            logger.info(f"Deleted question: {question_id}")
            self._refresh_stats()
            return True
        except Exception as e:
            logger.error(f"Failed to delete question: {e}")
            return False
    
    @tool
    def _search_questions_tool(
        self,
        query: str,
        n_results: int = 5,
        question_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        在题库中搜索题目
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            question_type: 题目类型过滤（example/exercise），可选
            
        Returns:
            搜索结果列表
        """
        self._init_chroma()
        
        if question_type:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"question_type": question_type}
            )
        else:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
        
        questions = []
        for i in range(len(results["ids"][0])):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            
            if "pages" in metadata and isinstance(metadata["pages"], str):
                try:
                    metadata["pages"] = json.loads(metadata["pages"])
                except:
                    metadata["pages"] = []
            
            questions.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i] if results["documents"] else "",
                "metadata": metadata
            })
        
        return questions
    
    @tool
    def _get_question_by_number_tool(self, question_number: str) -> Dict[str, Any]:
        """
        按题号查询题目
        
        Args:
            question_number: 题号
            
        Returns:
            题目信息
        """
        self._init_chroma()
        
        results = self.collection.get(
            where={"question_number": question_number}
        )
        
        if not results["ids"]:
            return {"error": f"Question not found: {question_number}"}
        
        metadata = results["metadatas"][0]
        if "pages" in metadata and isinstance(metadata["pages"], str):
            try:
                metadata["pages"] = json.loads(metadata["pages"])
            except:
                metadata["pages"] = []
        
        return {
            "id": results["ids"][0],
            "content": results["documents"][0] if results["documents"] else "",
            "metadata": metadata
        }
    
    @tool
    def _get_all_questions_tool(
        self,
        question_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取题库中的所有题目
        
        Args:
            question_type: 题目类型过滤（example/exercise），可选
            
        Returns:
            题目列表
        """
        self._init_chroma()
        
        if question_type:
            results = self.collection.get(
                where={"question_type": question_type}
            )
        else:
            results = self.collection.get()
        
        questions = []
        for i in range(len(results["ids"])):
            metadata = results["metadatas"][i]
            if "pages" in metadata and isinstance(metadata["pages"], str):
                try:
                    metadata["pages"] = json.loads(metadata["pages"])
                except:
                    metadata["pages"] = []
            
            questions.append({
                "id": results["ids"][i],
                "content": results["documents"][i] if results["documents"] else "",
                "metadata": metadata
            })
        
        return questions
    
    @tool
    def _get_question_stats_tool(self) -> Dict[str, Any]:
        """
        获取题库统计信息
        
        Returns:
            统计信息字典
        """
        self._refresh_stats()
        return self.question_stats.copy()
    
    @tool
    def _categorize_questions_tool(
        self,
        questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        对题目进行分类
        
        Args:
            questions: 题目列表
            
        Returns:
            分类后的题目列表
        """
        categorized = []
        
        for q in questions:
            q_copy = q.copy()
            q_num = q_copy.get("question_number", "")
            
            if q_num.startswith("例"):
                q_copy["question_type"] = "example"
                q_copy["type_label"] = "例题"
            else:
                q_copy["question_type"] = "exercise"
                q_copy["type_label"] = "习题"
            
            solution = q_copy.get("solution_content", "")
            q_copy["has_solution"] = bool(solution)
            
            categorized.append(q_copy)
        
        return categorized
    
    @tool
    def _analyze_solution_tool(
        self,
        solution_content: str
    ) -> Dict[str, Any]:
        """
        分析题目的解法
        
        Args:
            solution_content: 解法内容
            
        Returns:
            分析结果
        """
        if not solution_content:
            return {
                "has_solution": False,
                "solution_type": "none",
                "step_count": 0,
                "summary": "无解法内容"
            }
        
        system_prompt = self.prompt_manager.get_prompt("analyze_solution", "system_prompt")
        
        if not system_prompt:
            system_prompt = """请分析以下数学题目的解法内容，返回 JSON 格式：
{
    "solution_type": "解法类型：direct(直接计算)/proof(证明)/induction(归纳法)/other",
    "step_count": "步骤数量",
    "key_concepts": ["关键知识点列表"],
    "difficulty": "难度评估：easy/medium/hard",
    "summary": "解法简要总结"
}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"分析以下解法：\n{solution_content}"}
        ]
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 2048,
                    "temperature": 0.0
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result["choices"][0]["message"]["content"]
                json_str = self._extract_json(text, prefer_object=True)
                analysis = json.loads(json_str)
                analysis["has_solution"] = True
                return analysis
        except Exception as e:
            logger.error(f"Solution analysis failed: {e}")
        
        return {
            "has_solution": True,
            "solution_type": "unknown",
            "step_count": 1,
            "key_concepts": [],
            "difficulty": "unknown",
            "summary": solution_content[:200] if solution_content else ""
        }
    
    def process_pdf(
        self,
        pdf_path: str,
        start_page: int = 0,
        end_page: Optional[int] = None,
        enable_cross_page_merge: bool = True,
        auto_save: bool = True
    ) -> List[Dict[str, Any]]:
        """
        处理 PDF 文件，完整提取数学题目（含解法）
        
        Args:
            pdf_path: PDF 文件路径
            start_page: 起始页码（0-based）
            end_page: 结束页码（exclusive）
            enable_cross_page_merge: 是否启用跨页题目合并
            auto_save: 是否自动保存到题库
            
        Returns:
            提取的题目列表
        """
        logger.info(f"Processing PDF: {pdf_path}")
        if enable_cross_page_merge:
            logger.info("Cross-page merge enabled")
        
        images = self._pdf_to_images_tool.invoke({
            "pdf_path": pdf_path,
            "start_page": start_page,
            "end_page": end_page
        })
        pdf_name = Path(pdf_path).stem
        
        page_results = []
        
        for page_idx, img_path in enumerate(images):
            page_num = start_page + page_idx + 1
            logger.info(f"OCR processing page {page_num}: {img_path}")
            
            ocr_text = self._ocr_image_with_solution_tool.invoke({"image_path": img_path})
            logger.info(f"OCR result length: {len(ocr_text)}")
            
            questions = self._parse_questions_with_solution_tool.invoke({"ocr_text": ocr_text})
            logger.info(f"Parsed {len(questions)} questions on page {page_num}")
            
            for q in questions:
                q["source_image"] = img_path
                q["source_pdf"] = pdf_path
                q["page_num"] = page_num
            
            page_results.append({
                "page_num": page_num,
                "page_idx": page_idx,
                "image_path": img_path,
                "ocr_text": ocr_text,
                "questions": questions
            })
        
        if enable_cross_page_merge and len(page_results) > 1:
            logger.info("Merging cross-page questions...")
            merged_questions = self._merge_cross_page_questions_tool.invoke({"page_results": page_results})
            logger.info(f"After merge: {len(merged_questions)} questions")
            
            all_questions = merged_questions
        else:
            all_questions = []
            for pr in page_results:
                all_questions.extend(pr["questions"])
        
        all_questions = self._categorize_questions_tool.invoke({"questions": all_questions})
        
        if auto_save and all_questions:
            self._batch_add_questions_tool.invoke({
                "questions": all_questions,
                "source": pdf_name
            })
        
        logger.info(f"Total questions extracted: {len(all_questions)}")
        return all_questions
    
    def add_question(
        self,
        question_number: str,
        question_type: str,
        question_content: str,
        answer_content: str = "",
        solution_content: str = "",
        source: str = ""
    ) -> str:
        """
        添加单道题目到题库
        
        Args:
            question_number: 题号
            question_type: 题目类型（example/exercise）
            question_content: 题目内容
            answer_content: 答案内容
            solution_content: 解法内容
            source: 来源
            
        Returns:
            题目 ID
        """
        return self._add_question_to_bank_tool.invoke({
            "question_number": question_number,
            "question_type": question_type,
            "question_content": question_content,
            "answer_content": answer_content,
            "solution_content": solution_content,
            "source": source
        })
    
    def batch_add_questions(
        self,
        questions: List[Dict[str, Any]],
        source: str = ""
    ) -> List[str]:
        """
        批量添加题目到题库
        
        Args:
            questions: 题目列表
            source: 来源
            
        Returns:
            题目 ID 列表
        """
        return self._batch_add_questions_tool.invoke({
            "questions": questions,
            "source": source
        })
    
    def search_questions(
        self,
        query: str,
        n_results: int = 5,
        question_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        搜索题目
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            question_type: 题目类型过滤
            
        Returns:
            搜索结果列表
        """
        return self._search_questions_tool.invoke({
            "query": query,
            "n_results": n_results,
            "question_type": question_type
        })
    
    def get_all_questions(self, question_type: str = None) -> List[Dict[str, Any]]:
        """
        获取所有题目
        
        Args:
            question_type: 题目类型过滤
            
        Returns:
            题目列表
        """
        return self._get_all_questions_tool.invoke({"question_type": question_type})
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取题库统计
        
        Returns:
            统计信息
        """
        return self._get_question_stats_tool.invoke({})
    
    def get_question_by_number(self, question_number: str) -> Dict[str, Any]:
        """
        按题号查询题目
        
        Args:
            question_number: 题号
            
        Returns:
            题目信息
        """
        return self._get_question_by_number_tool.invoke({"question_number": question_number})
    
    def update_question(
        self,
        question_id: str,
        **updates
    ) -> bool:
        """
        更新题目
        
        Args:
            question_id: 题目 ID
            **updates: 更新字段
            
        Returns:
            是否成功
        """
        return self._update_question_tool.invoke({
            "question_id": question_id,
            **updates
        })
    
    def delete_question(self, question_id: str) -> bool:
        """
        删除题目
        
        Args:
            question_id: 题目 ID
            
        Returns:
            是否成功
        """
        return self._delete_question_tool.invoke({"question_id": question_id})
