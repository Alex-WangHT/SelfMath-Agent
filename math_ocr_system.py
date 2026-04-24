import os
import sys
import argparse
import base64
import json
import fitz
import chromadb
import requests
import logging
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Any, Optional
from chromadb.utils import embedding_functions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class MathOCRSystem:
    def __init__(self):
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        self.base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        self.model = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen3-Omni-30B-A3B-Captioner")
        self.db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        self.collection_name = os.getenv("CHROMA_COLLECTION", "math_questions")
        
        self.temp_dir = Path("./data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.db = None
        self.collection = None
        
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment variables")
    
    def _init_chroma(self):
        if self.collection is None:
            self.db = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.db.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
            logger.info(f"ChromaDB initialized at {self.db_path}")
    
    def pdf_to_images(self, pdf_path: str, start_page: int = 0, end_page: Optional[int] = None) -> List[str]:
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
    
    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def ocr_image(self, image_path: str) -> str:
        base64_img = self._encode_image(image_path)
        
        system_prompt = """你是一个专业的数学OCR识别助手。请仔细识别图片中的数学内容：
1. 完整识别所有数学公式，使用LaTeX格式
2. 识别所有文字说明和题目要求
3. 保持原有的题目结构和编号
4. 如果有多个题目，分别识别并标注题号

特别注意题目类型和边界标识：
- 例题：以"例"字开头的题目，如"例1.1"、"例2.3.1"等，这类题目通常包含题目和答案两部分
- 习题：以数字编号开头的题目，如"1.1.1"、"2.3.4"等，这类题目通常只有题目没有答案

重要：请完整保留所有内容，包括题目之间的过渡文字，这些信息对于判断题目是否跨页非常重要。

请仅返回识别到的内容。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "识别这张图片中的数学内容。"},
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
    
    def parse_questions(self, ocr_text: str) -> List[Dict[str, Any]]:
        system_prompt = """你是数学题目解析助手。请将以下数学内容解析为JSON数组。

【极其重要的分类规则】

类型1：例题(example)
- 识别特征：题号以"例"字开头，如"例1.1"、"例2.3.1"等
- 处理规则：必须完整提取【题目内容】和【答案内容】两部分
- 答案起始标识："【答案】"、"解："、"证明："、"分析："、"解答："、"答案："

类型2：习题(exercise)
- 识别特征：题号以纯数字开头，如"1.1.1"、"2.3.4"等
- 处理规则：只提取【题目内容】，绝对不要提取答案！即使内容中有答案部分，也必须忽略！
- answer_content字段必须设置为空字符串""
- 另外：习题中不许录入提示词条，只保留纯粹的题目内容

【题目边界判断规则】
1. 新的题号（以"例"或数字开头）标志着新题目的开始
2. 如果内容在页面末尾突然中断，没有新的题号开始，则标记is_incomplete=true
3. 判断题目是否完整：如果当前内容以新的题号开头，则上一个题目完整

【输出格式要求】
[
  {
    "question_number": "题号，如'例1.1'或'1.1.1'",
    "question_type": "题目类型，只能是'example'或'exercise'",
    "question_content": "题目内容（LaTeX公式），习题只保留纯粹的题目内容，删除所有提示词条",
    "answer_content": "答案内容（仅例题有，LaTeX公式），习题此字段必须为空字符串''",
    "raw_text": "该题目的完整原始文本",
    "is_incomplete": "布尔值，如果题目可能跨页（内容不完整）则为true，否则为false",
    "page_hint": "该题目的页码范围提示，如'第3-4页'"
  }
]

【绝对必须遵守的规则】
1. 例题(question_type='example')：必须同时提取题目内容和答案内容，answer_content不能空
2. 习题(question_type='exercise')：只提取题目内容，answer_content必须是空字符串""！即使原文有答案也必须忽略！
3. 习题的question_content中绝对不能包含任何提示词条（如"提示"、"思路"、"注意"等）
4. 仔细判断每个题目是否完整，如果内容中断且没有新的题号开始，标记is_incomplete=true
5. 只输出JSON数组，不要输出任何其他文字、解释或markdown格式"""
        
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
    
    def _extract_json(self, text: str) -> str:
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
    
    def _detect_question_patterns(self, text: str) -> List[Dict[str, Any]]:
        import re
        
        patterns = []
        
        example_pattern = r'例\d+(\.\d+)*'
        for match in re.finditer(example_pattern, text):
            patterns.append({
                "type": "example",
                "number": match.group(),
                "start_index": match.start(),
                "end_index": match.end()
            })
        
        exercise_pattern = r'(?<![\.0-9])\d+\.\d+(\.\d+)+(?!\d)'
        for match in re.finditer(exercise_pattern, text):
            patterns.append({
                "type": "exercise",
                "number": match.group(),
                "start_index": match.start(),
                "end_index": match.end()
            })
        
        patterns.sort(key=lambda x: x["start_index"])
        return patterns
    
    def _is_potential_question_start(self, text: str) -> bool:
        import re
        
        if re.match(r'^\s*例\d+', text):
            return True
        
        if re.match(r'^\s*\d+\.\d+\.\d+', text):
            return True
        
        return False
    
    def _merge_cross_page_questions(
        self,
        page_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
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
    
    def _parse_merged_question(
        self,
        question: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged_text = question.get("raw_text", "")
        
        system_prompt = """你是数学题目整合助手。以下是一道可能跨越多页的数学题目的完整合并文本。

请根据以下规则进行整合：
1. 去除页码标记（如"[页末延续]"）和重复内容
2. 合并题目内容和答案内容，确保逻辑连贯
3. 保持LaTeX公式的正确性
4. 判断题目类型和完整性

输入格式示例：
{
  "question_number": "例1.1",
  "question_type": "example",
  "question_content": "第一页的题目内容...",
  "answer_content": "第一页的答案...",
  "raw_text": "完整合并的原始文本...",
  "pages": [1, 2, 3]
}

输出格式：
{
  "question_number": "例1.1",
  "question_type": "example",
  "question_content": "整合后的完整题目内容",
  "answer_content": "整合后的完整答案内容",
  "raw_text": "完整原始文本",
  "pages": [1, 2, 3],
  "page_count": 3
}

请直接输出JSON，不要其他内容。"""
        
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
            json_str = self._extract_json(text)
            merged = json.loads(json_str)
            
            for key in ["question_number", "question_type", "question_content", "answer_content", "raw_text"]:
                if key not in merged or not merged[key]:
                    merged[key] = question.get(key, "")
            
            merged["pages"] = question.get("pages", [question.get("page_num", 0)])
            merged["page_count"] = len(merged["pages"])
            
            return merged
        except json.JSONDecodeError:
            logger.error(f"Merge parse failed: {text}")
            return question
    
    def _filter_hint_keywords(self, text: str) -> str:
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
    
    def _post_process_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
    
    def store_questions(self, questions: List[Dict[str, Any]], source: str = ""):
        self._init_chroma()
        
        if not questions:
            return
        
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
    
    def process_pdf(
        self,
        pdf_path: str,
        start_page: int = 0,
        end_page: Optional[int] = None,
        enable_cross_page_merge: bool = True
    ) -> List[Dict[str, Any]]:
        logger.info(f"Processing PDF: {pdf_path}")
        if enable_cross_page_merge:
            logger.info("Cross-page merge enabled")
        
        images = self.pdf_to_images(pdf_path, start_page, end_page)
        pdf_name = Path(pdf_path).stem
        
        page_results = []
        
        for page_idx, img_path in enumerate(images):
            page_num = start_page + page_idx + 1
            logger.info(f"OCR processing page {page_num}: {img_path}")
            
            ocr_text = self.ocr_image(img_path)
            logger.info(f"OCR result length: {len(ocr_text)}")
            
            questions = self.parse_questions(ocr_text)
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
            merged_questions = self._merge_cross_page_questions(page_results)
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
            self.store_questions(all_questions, source=pdf_name)
        
        logger.info(f"Total questions extracted: {len(all_questions)}")
        return all_questions
    
    def search_questions(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
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
    
    def get_all_questions(self) -> List[Dict[str, Any]]:
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


def _cli_process(args):
    system = MathOCRSystem()
    
    if not os.path.exists(args.pdf):
        print(f"Error: File not found: {args.pdf}")
        sys.exit(1)
    
    start_page = args.start if args.start is not None else 0
    end_page = args.end
    
    print(f"Processing PDF: {args.pdf}")
    print(f"Pages: {start_page + 1} - {end_page if end_page else 'end'}")
    print(f"Cross-page merge: {'Enabled' if not args.no_cross_page else 'Disabled'}")
    
    questions = system.process_pdf(
        args.pdf, 
        start_page, 
        end_page,
        enable_cross_page_merge=not args.no_cross_page
    )
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print(f"Results saved to: {args.output}")
    
    example_count = sum(1 for q in questions if q.get('question_type') == 'example')
    exercise_count = sum(1 for q in questions if q.get('question_type') == 'exercise')
    cross_page_count = sum(1 for q in questions if len(q.get('pages', [])) > 1)
    
    print(f"\nTotal questions extracted: {len(questions)}")
    print(f"  - Examples (例题): {example_count}")
    print(f"  - Exercises (习题): {exercise_count}")
    if cross_page_count > 0:
        print(f"  - Cross-page questions (跨页题目): {cross_page_count}")
    
    if questions and not args.quiet:
        print("\n" + "=" * 60)
        print("Extracted Questions Preview:")
        print("=" * 60)
        for i, q in enumerate(questions[:3]):
            q_type = q.get('question_type', 'exercise')
            type_label = "例题" if q_type == 'example' else "习题"
            pages = q.get('pages', [q.get('page_num', 0)])
            page_info = f" (跨页: {pages})" if len(pages) > 1 else f" (页: {pages[0]})"
            
            print(f"\n--- Question {i + 1} [{type_label}]{page_info} ---")
            print(f"Number: {q.get('question_number', 'N/A')}")
            print(f"Type: {q_type}")
            print(f"Content: {q.get('question_content', 'N/A')[:200]}...")
            answer = q.get('answer_content', '')
            if answer:
                print(f"Answer: {answer[:150]}...")
        if len(questions) > 3:
            print(f"\n... and {len(questions) - 3} more questions")


def _cli_search(args):
    system = MathOCRSystem()
    
    results = system.search_questions(args.query, args.limit)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Results saved to: {args.output}")
    
    if not args.quiet:
        print(f"\nFound {len(results)} results for query: {args.query}")
        print("=" * 60)
        for i, r in enumerate(results):
            q_type = r['metadata'].get('question_type', 'exercise')
            type_label = "例题" if q_type == 'example' else "习题"
            print(f"\n--- Result {i + 1} [{type_label}] ---")
            print(f"ID: {r['id']}")
            print(f"Number: {r['metadata'].get('question_number', 'N/A')}")
            print(f"Type: {q_type}")
            print(f"Content: {r['content']}")
            print(f"Source: {r['metadata'].get('source', 'N/A')}")


def _cli_list(args):
    system = MathOCRSystem()
    
    questions = system.get_all_questions()
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print(f"Results saved to: {args.output}")
    
    if not args.quiet:
        example_count = sum(1 for q in questions if q['metadata'].get('question_type') == 'example')
        exercise_count = sum(1 for q in questions if q['metadata'].get('question_type') == 'exercise')
        
        print(f"\nTotal questions in database: {len(questions)}")
        print(f"  - Examples (例题): {example_count}")
        print(f"  - Exercises (习题): {exercise_count}")
        
        if questions:
            print("=" * 60)
            limit = args.limit if args.limit else len(questions)
            for i, q in enumerate(questions[:limit]):
                q_type = q['metadata'].get('question_type', 'exercise')
                type_label = "例题" if q_type == 'example' else "习题"
                print(f"\n--- Question {i + 1} [{type_label}] ---")
                print(f"ID: {q['id']}")
                print(f"Number: {q['metadata'].get('question_number', 'N/A')}")
                print(f"Type: {q_type}")
                print(f"Content: {q['content'][:150]}...")
                print(f"Source: {q['metadata'].get('source', 'N/A')}")


def _main():
    parser = argparse.ArgumentParser(
        description="Math OCR System - Extract and store math questions from PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with cross-page merge (default)
  python math_ocr_system.py process --pdf exercises.pdf --start 0 --end 10
  
  # Disable cross-page merge
  python math_ocr_system.py process --pdf book.pdf --no-cross-page
  
  # Save results to JSON
  python math_ocr_system.py process --pdf book.pdf -o results.json
  
  # Search questions
  python math_ocr_system.py search --query "求极限" --limit 5
  
  # List all questions
  python math_ocr_system.py list --limit 10
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    process_parser = subparsers.add_parser("process", help="Process PDF and extract questions")
    process_parser.add_argument("--pdf", required=True, help="Path to PDF file")
    process_parser.add_argument("--start", type=int, help="Start page number (0-based)")
    process_parser.add_argument("--end", type=int, help="End page number (exclusive)")
    process_parser.add_argument("--no-cross-page", action="store_true", 
                               help="Disable cross-page question merging")
    process_parser.add_argument("-o", "--output", help="Output JSON file path")
    process_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")
    
    search_parser = subparsers.add_parser("search", help="Search questions in vector database")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Number of results (default: 5)")
    search_parser.add_argument("-o", "--output", help="Output JSON file path")
    search_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")
    
    list_parser = subparsers.add_parser("list", help="List all questions in database")
    list_parser.add_argument("--limit", type=int, help="Limit number of results to display")
    list_parser.add_argument("-o", "--output", help="Output JSON file path")
    list_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    try:
        if args.command == "process":
            _cli_process(args)
        elif args.command == "search":
            _cli_search(args)
        elif args.command == "list":
            _cli_list(args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    _main()
