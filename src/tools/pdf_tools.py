"""
PDF 处理工具模块
- PDFToImagesTool: 将 PDF 转换为图片的工具类
- pdf_to_images: 便捷函数
"""

import os
import fitz
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class PDFToImagesTool:
    """
    PDF 转图片工具类
    
    功能：
    - 将 PDF 文件的指定页码范围转换为高清图片
    - 支持自定义 DPI（默认 2x 缩放）
    - 自动创建临时目录存储图片
    
    使用场景：
    - PDF 文档的 OCR 预处理
    - 图片格式的数学公式识别
    - 跨平台文档展示
    
    依赖：
    - PyMuPDF (fitz): 用于渲染 PDF 页面
    
    示例：
        >>> tool = PDFToImagesTool(temp_dir="./temp")
        >>> images = tool.convert("document.pdf", start_page=0, end_page=5)
        >>> print(f"转换了 {len(images)} 页")
    """
    
    def __init__(self, temp_dir: str = "./data/temp"):
        """
        初始化 PDF 转图片工具
        
        Args:
            temp_dir: 临时图片存储目录，默认 "./data/temp"
                     如果目录不存在，会自动创建
        
        注意：
            临时目录中的图片不会自动清理，建议定期清理
            或在使用完毕后手动删除
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"PDFToImagesTool 初始化完成，临时目录: {temp_dir}")
    
    def convert(
        self,
        pdf_path: str,
        start_page: int = 0,
        end_page: Optional[int] = None,
        dpi: float = 2.0
    ) -> List[str]:
        """
        将 PDF 文件转换为图片
        
        【转换流程】
        1. 打开 PDF 文件，获取总页数
        2. 校验页码范围（自动处理越界情况）
        3. 逐页渲染为图片（使用指定 DPI）
        4. 保存到临时目录，返回图片路径列表
        
        Args:
            pdf_path: PDF 文件的完整路径
            start_page: 起始页码（0-based，从 0 开始）
            end_page: 结束页码（exclusive，不包含此页）
                     如果为 None，则转换到最后一页
            dpi: 渲染缩放比例，默认 2.0（对应 144 DPI）
                建议值：
                - 1.0: 72 DPI（适合快速预览）
                - 2.0: 144 DPI（适合普通 OCR）
                - 3.0: 216 DPI（适合高精度公式识别）
        
        Returns:
            转换后的图片路径列表，按页码顺序排列
        
        Raises:
            FileNotFoundError: 当 pdf_path 不存在时抛出
        
        示例：
            >>> # 转换前 10 页
            >>> images = tool.convert("book.pdf", start_page=0, end_page=10, dpi=2.0)
            >>> # 转换整个 PDF
            >>> all_images = tool.convert("book.pdf")
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        logger.info(f"打开 PDF: {pdf_path}，总页数: {total_pages}")
        
        if end_page is None:
            end_page = total_pages
        
        start_page = max(0, start_page)
        end_page = min(total_pages, end_page)
        
        image_paths = []
        pdf_name = Path(pdf_path).stem
        
        for page_num in range(start_page, end_page):
            page = doc[page_num]
            mat = fitz.Matrix(dpi, dpi)
            pix = page.get_pixmap(matrix=mat)
            
            image_path = self.temp_dir / f"{pdf_name}_page_{page_num + 1}.png"
            pix.save(str(image_path))
            image_paths.append(str(image_path))
            
            logger.info(f"已处理第 {page_num + 1}/{total_pages} 页，保存到: {image_path}")
        
        doc.close()
        logger.info(f"PDF 转图片完成，共生成 {len(image_paths)} 张图片")
        return image_paths


def pdf_to_images(
    pdf_path: str,
    start_page: int = 0,
    end_page: Optional[int] = None,
    temp_dir: str = "./data/temp",
    dpi: float = 2.0
) -> List[str]:
    """
    PDF 转图片的便捷函数
    
    这是 PDFToImagesTool 类的简化封装，适合一次性使用。
    
    Args:
        pdf_path: PDF 文件路径
        start_page: 起始页码（0-based）
        end_page: 结束页码（exclusive）
        temp_dir: 临时图片存储目录
        dpi: 渲染缩放比例
    
    Returns:
        转换后的图片路径列表
    
    示例：
        >>> images = pdf_to_images("document.pdf", start_page=0, end_page=5)
        >>> for img in images:
        >>>     print(f"图片: {img}")
    """
    tool = PDFToImagesTool(temp_dir=temp_dir)
    return tool.convert(pdf_path, start_page, end_page, dpi)
