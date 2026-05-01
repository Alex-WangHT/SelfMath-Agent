"""
程序启动入口（根目录）

这个文件是为了向后兼容。
新的主入口在：src/services/app.py

运行方式：
  python app.py          # 向后兼容
  python src/services/app.py  # 新的入口
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    from src.services.app import main
    main()
