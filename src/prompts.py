import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class PromptManager:
    """
    提示词管理器，实现 Agent-Prompt 解耦
    支持从 JSON 或 Markdown 文件加载提示词
    """
    
    def __init__(self, prompts_path: Optional[str] = None):
        """
        初始化提示词管理器
        
        Args:
            prompts_path: 提示词文件路径，如果为 None 则从环境变量或默认路径加载
        """
        self.prompts_path = self._resolve_prompts_path(prompts_path)
        self.prompts = self._load_prompts()
    
    def _resolve_prompts_path(self, prompts_path: Optional[str]) -> Path:
        """
        解析提示词文件路径
        
        Args:
            prompts_path: 用户提供的路径
            
        Returns:
            解析后的 Path 对象
        """
        if prompts_path is None:
            prompts_path = os.getenv("PROMPTS_PATH", "./prompts.json")
        
        return Path(prompts_path)
    
    def _load_prompts(self) -> Dict[str, Any]:
        """
        从文件加载提示词
        
        Returns:
            提示词字典
        """
        if not self.prompts_path.exists():
            logger.warning(f"Prompts file not found at {self.prompts_path}")
            return {}
        
        try:
            file_ext = self.prompts_path.suffix.lower()
            
            if file_ext == ".json":
                with open(self.prompts_path, "r", encoding="utf-8") as f:
                    prompts = json.load(f)
                logger.info(f"Loaded prompts from JSON: {self.prompts_path}")
            elif file_ext == ".md":
                prompts = self._parse_markdown_prompts(self.prompts_path)
                logger.info(f"Loaded prompts from Markdown: {self.prompts_path}")
            else:
                logger.warning(f"Unknown prompt file format: {file_ext}")
                return {}
            
            return prompts
        except Exception as e:
            logger.error(f"Failed to load prompts from {self.prompts_path}: {e}")
            return {}
    
    def _parse_markdown_prompts(self, file_path: Path) -> Dict[str, Any]:
        """
        解析 Markdown 格式的提示词文件
        
        Args:
            file_path: Markdown 文件路径
            
        Returns:
            提示词字典
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        result = {}
        
        current_module = None
        current_field = None
        current_code_block = []
        in_code_block = False
        
        for line in lines:
            if line.startswith("```"):
                if in_code_block:
                    if current_module and current_field:
                        code_content = "\n".join(current_code_block).strip()
                        if current_module not in result:
                            result[current_module] = {}
                        result[current_module][current_field] = code_content
                    current_code_block = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue
            
            if in_code_block:
                current_code_block.append(line)
                continue
            
            if line.startswith("## "):
                current_module = line[3:].strip()
                if current_module.startswith("模块: "):
                    current_module = current_module[4:].strip()
                current_field = None
                continue
            
            if line.startswith("### "):
                field_name = line[4:].strip()
                if field_name in ["system_prompt", "user_text", "value"]:
                    current_field = field_name
                else:
                    current_field = None
                continue
        
        return result
    
    def get_prompt(self, module: str, field: Optional[str] = None) -> Any:
        """
        获取提示词
        
        Args:
            module: 模块名
            field: 字段名，如果为 None 则返回整个模块
            
        Returns:
            提示词内容
        """
        module_prompt = self.prompts.get(module, {})
        
        if field:
            return module_prompt.get(field, "")
        
        return module_prompt
    
    def get_prompt_or_raise(self, module: str, field: str) -> str:
        """
        获取提示词，如果不存在则抛出异常
        
        Args:
            module: 模块名
            field: 字段名
            
        Returns:
            提示词内容
            
        Raises:
            ValueError: 如果提示词不存在
        """
        prompt = self.get_prompt(module, field)
        
        if not prompt:
            raise ValueError(f"Prompt not found: module='{module}', field='{field}'")
        
        return prompt
    
    def reload(self) -> None:
        """
        重新加载提示词
        """
        self.prompts = self._load_prompts()
        logger.info("Prompts reloaded")
    
    def list_modules(self) -> list:
        """
        列出所有可用的模块
        
        Returns:
            模块名列表
        """
        return list(self.prompts.keys())
    
    def list_fields(self, module: str) -> list:
        """
        列出指定模块的所有字段
        
        Args:
            module: 模块名
            
        Returns:
            字段名列表
        """
        module_prompt = self.prompts.get(module, {})
        return list(module_prompt.keys())
