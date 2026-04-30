import os
import base64
import json
import fitz
import chromadb
import requests
import logging
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from chromadb.utils import embedding_functions

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from .prompts import PromptManager

logger = logging.getLogger(__name__)

load_dotenv()


class MathOCRAgent:
    """
    数学 OCR Agent，用于习题集的录用和管理
    采用 LangChain Agent 架构，支持工具调用和智能决策
    """
    
    def __init__(
        self,
        prompt_manager: Optional[PromptManager] = None,
        prompts_path: Optional[str] = None
    ):
        """
        初始化 MathOCRAgent
        
        Args:
            prompt_manager: 提示词管理器，如果为 None 则自动创建
            prompts_path: 提示词文件路径，仅在 prompt_manager 为 None 时使用
        """
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        self.base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        self.model = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen3-Omni-30B-A3B-Captioner")
        self.db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        self.collection_name = os.getenv("CHROMA_COLLECTION", "math_questions")
        
        self.temp_dir = Path("./data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.db = None
        self.collection = None
        
        self.prompt_manager = prompt_manager or PromptManager(prompts_path)
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent_executor()
        
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment variables")
    
    def _create_tools(self) -> List:
        """
        创建 Agent 可用的工具列表
        
        Returns:
            工具列表
        """
        tools = [
            self._pdf_to_images_tool,
            self._ocr_image_tool,
            self._parse_questions_tool,
            self._merge_cross_page_questions_tool,
            self._store_questions_tool,
            self._search_questions_tool,
            self._get_all_questions_tool
        ]
        
        return tools
    
    def _create_agent_executor(self) -> AgentExecutor:
        """
        创建 Agent 执行器
        
        Returns:
            AgentExecutor 实例
        """
        system_prompt = self.prompt_manager.get_prompt("agent", "system_prompt")
        
        if not system_prompt:
            system_prompt = """你是一个专业的数学 OCR Agent，负责习题集的录用和管理。
你可以使用以下工具：
1. pdf_to_images: 将 PDF 文件转换为图片
2. ocr_image: 对图片进行 OCR 识别，提取数学内容
3. parse_questions: 解析 OCR 结果，提取数学题目
4. merge_cross_page_questions: 合并跨页的数学题目
5. store_questions: 将提取的题目存储到向量数据库
6. search_questions: 在向量数据库中搜索题目
7. get_all_questions: 获取数据库中的所有题目

当用户要求处理 PDF 时，你需要：
1. 先将 PDF 转换为图片
2. 对每张图片进行 OCR 识别
3. 解析 OCR 结果提取题目
4. 合并跨页题目
5. 将题目存储到数据库

当用户要求搜索题目时，使用 search_questions 工具。
当用户要求查看所有题目时，使用 get_all_questions 工具。

请根据用户的需求，智能地选择和调用工具。"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("agent_scratchpad", "{agent_scratchpad}")
        ])
        
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.0
        )
        
        agent = create_tool_calling_agent(llm, self.tools, prompt)
        
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def _init_chroma(self):
        """初始化 ChromaDB 连接"""
        if self.collection is None:
            self.db = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.db.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
            logger.info(f"ChromaDB initialized at {self.db_path}")
    
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
    def _ocr_image_tool(self, image_path: str) -> str:
        """
        对图片进行 OCR 识别，提取数学内容
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            OCR 识别结果文本
        """
        base64_img = self._encode_image(image_path)
        
        system_prompt = self.prompt_manager.get_prompt_or_raise("ocr_image", "system_prompt")
        user_text = self.prompt_manager.get_prompt("ocr_image", "user_text") or "识别这张图片中的数学内容。"
        
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
                "max_tokens": 4096,
                "temperature": 0.0
            },
            timeout=120
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
    def _parse_questions_tool(self, ocr_text: str) -> List[Dict[str, Any]]:
        """
        解析 OCR 结果，提取数学题目
        
        Args:
            ocr_text: OCR 识别结果文本
            
        Returns:
            解析后的题目列表
        """
        system_prompt = self.prompt_manager.get_prompt_or_raise("parse_questions", "system_prompt")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"解析以下内容：\n{ocr_text}"}
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
                "max_tokens": 4096,
                "temperature": 0.0
            },
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"Parse API failed: {response.status_code} - {response.text}")
        
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        
        try:
            json_str = self._extract_json(text)
            questions = json.loads(json_str)
            
            for q in questions:
                q_type = q.get("question_type", "")
                q_num = q.get("question_number", "")
                
                if q_num.startswith("例"):
                    q["question_type"] = "example"
                elif q_num and (q_num[0].isdigit() or (len(q_num) > 1 and q_num[1].isdigit())):
                    q["question_type"] = "exercise"
                
                if q.get("question_type") == "exercise":
                    q["answer_content"] = ""
            
            return questions
        except json.JSONDecodeError:
            logger.error(f"Parse failed: {text}")
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
            page_results: 每页的解析结果列表，每个元素包含 page_num, questions 等信息
            
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
            ocr_text = page_info.get("ocr_text", "")
            
            for q in questions:
                is_incomplete = q.get("is_incomplete", False)
                q_number = q.get("question_number", "")
                
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
            
            if pending_question is not None and not questions:
                pending_question["question_content"] = (
                    pending_question.get("question_content", "") + 
                    "\n[页末延续]"
                )
        
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
    def _store_questions_tool(
        self,
        questions: List[Dict[str, Any]],
        source: str = ""
    ) -> int:
        """
        将提取的题目存储到向量数据库
        
        Args:
            questions: 题目列表
            source: 来源标识（如 PDF 文件名）
            
        Returns:
            存储的题目数量
        """
        self._init_chroma()
        
        if not questions:
            return 0
        
        questions = self._post_process_questions(questions)
        
        ids = []
        documents = []
        metadatas = []
        
        for i, q in enumerate(questions):
            qid = f"q_{source}_{hash(q.get('question_content', ''))}_{i}"
            ids.append(qid)
            
            content_parts = [q.get("question_content", "")]
            answer = q.get("answer_content", "")
            if answer:
                content_parts.append(f"\n【答案】{answer}")
            documents.append("\n".join(content_parts))
            
            metadatas.append({
                "question_number": q.get("question_number", ""),
                "question_type": q.get("question_type", "exercise"),
                "answer_content": q.get("answer_content", ""),
                "raw_text": q.get("raw_text", ""),
                "source": source
            })
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Stored {len(questions)} questions to vector DB")
        
        return len(questions)
    
    def _post_process_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """后处理题目"""
        processed = []
        
        for q in questions:
            q_copy = q.copy()
            question_type = q_copy.get("question_type", "")
            
            if question_type == "exercise":
                original_content = q_copy.get("question_content", "")
                filtered_content = self._filter_hint_keywords(original_content)
                q_copy["question_content"] = filtered_content
                q_copy["answer_content"] = ""
            
            q_copy.setdefault("question_type", "exercise")
            q_copy.setdefault("answer_content", "")
            
            processed.append(q_copy)
        
        return processed
    
    def _filter_hint_keywords(self, text: str) -> str:
        """过滤提示词"""
        hint_patterns = [
            "提示", "思路", "注意", "说明", "分析", "思考",
            "【提示】", "【思路】", "【注意】", "【说明】",
            "提示：", "思路：", "注意：", "说明：",
            "提示:", "思路:", "注意:", "说明:"
        ]
        
        lines = text.split("\n")
        filtered_lines = []
        in_hint_section = False
        
        for line in lines:
            is_hint_line = False
            for pattern in hint_patterns:
                if pattern in line:
                    is_hint_line = True
                    in_hint_section = True
                    break
            
            if is_hint_line:
                continue
            
            if in_hint_section:
                if line.strip() == "" or line.strip().startswith("例") or \
                   (line.strip() and line.strip()[0].isdigit() and "." in line.strip()):
                    in_hint_section = False
                else:
                    continue
            
            filtered_lines.append(line)
        
        return "\n".join(filtered_lines).strip()
    
    @tool
    def _search_questions_tool(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在向量数据库中搜索题目
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        self._init_chroma()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        questions = []
        for i in range(len(results["ids"][0])):
            questions.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
            })
        
        return questions
    
    @tool
    def _get_all_questions_tool(self) -> List[Dict[str, Any]]:
        """
        获取数据库中的所有题目
        
        Returns:
            所有题目列表
        """
        self._init_chroma()
        
        results = self.collection.get()
        questions = []
        
        for i in range(len(results["ids"])):
            questions.append({
                "id": results["ids"][i],
                "content": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {}
            })
        
        return questions
    
    def process_pdf(
        self,
        pdf_path: str,
        start_page: int = 0,
        end_page: Optional[int] = None,
        enable_cross_page_merge: bool = True
    ) -> List[Dict[str, Any]]:
        """
        处理 PDF 文件，提取数学题目
        
        Args:
            pdf_path: PDF 文件路径
            start_page: 起始页码（0-based）
            end_page: 结束页码（exclusive）
            enable_cross_page_merge: 是否启用跨页题目合并
            
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
            
            ocr_text = self._ocr_image_tool.invoke({"image_path": img_path})
            logger.info(f"OCR result length: {len(ocr_text)}")
            
            questions = self._parse_questions_tool.invoke({"ocr_text": ocr_text})
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
            
            final_questions = []
            for q in merged_questions:
                pages = q.get("pages", [q.get("page_num", 0)])
                if len(pages) > 1:
                    logger.info(f"Question {q.get('question_number', 'N/A')} spans pages: {pages}")
                    merged_q = self._parse_merged_question(q)
                    final_questions.append(merged_q)
                else:
                    final_questions.append(q)
            
            all_questions = final_questions
        else:
            all_questions = []
            for pr in page_results:
                all_questions.extend(pr["questions"])
        
        if all_questions:
            self._store_questions_tool.invoke({
                "questions": all_questions,
                "source": pdf_name
            })
        
        logger.info(f"Total questions extracted: {len(all_questions)}")
        return all_questions
    
    def _parse_merged_question(
        self,
        question: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析合并后的跨页题目"""
        system_prompt = self.prompt_manager.get_prompt_or_raise("parse_merged_question", "system_prompt")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(question, ensure_ascii=False, indent=2)}
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
                "max_tokens": 4096,
                "temperature": 0.0
            },
            timeout=120
        )
        
        if response.status_code != 200:
            logger.error(f"Merge API failed: {response.status_code}")
            return question
        
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        
        try:
            json_str = self._extract_json(text, prefer_object=True)
            merged = json.loads(json_str)
            
            if isinstance(merged, list) and len(merged) > 0:
                merged = merged[0]
            
            if not isinstance(merged, dict):
                logger.error(f"Merge result is not a dict: {type(merged)}")
                return question
            
            for key in ["question_number", "question_type", "question_content", "answer_content", "raw_text"]:
                if key not in merged or not merged[key]:
                    merged[key] = question.get(key, "")
            
            merged["pages"] = question.get("pages", [question.get("page_num", 0)])
            merged["page_count"] = len(merged["pages"])
            
            return merged
        except json.JSONDecodeError as e:
            logger.error(f"Merge parse failed: {e}, text: {text[:200]}")
            return question
    
    def search_questions(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索题目
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        return self._search_questions_tool.invoke({
            "query": query,
            "n_results": n_results
        })
    
    def get_all_questions(self) -> List[Dict[str, Any]]:
        """
        获取所有题目
        
        Returns:
            所有题目列表
        """
        return self._get_all_questions_tool.invoke({})
    
    def invoke(self, input: str) -> Dict[str, Any]:
        """
        调用 Agent 执行任务
        
        Args:
            input: 用户输入
            
        Returns:
            Agent 执行结果
        """
        return self.agent_executor.invoke({"input": input})
    
    def run(self, input: str) -> str:
        """
        运行 Agent（简化接口）
        
        Args:
            input: 用户输入
            
        Returns:
            Agent 输出结果
        """
        result = self.invoke(input)
        return result.get("output", "")
