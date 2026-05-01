"""
程序启动入口

这是整个应用的主入口文件。
运行方式：python src/services/app.py

架构说明：
- src/interface/: 接口定义层（数据模型、接口协议）
- src/services/: Web表现层（Flask路由、Mock服务实现）

这两个层完全解耦，不依赖任何真实的Agent实现。
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

USE_MOCK_AGENTS = os.getenv("USE_MOCK_AGENTS", "True").lower() == "true"


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("  Math Learning Agent")
    logger.info("=" * 60)
    logger.info(f"  USE_MOCK_AGENTS: {USE_MOCK_AGENTS}")
    
    # 导入必要的模块
    from src.services.flask_routes import create_app, run_app
    
    # 创建Flask应用
    app = create_app()
    
    # 获取配置
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    # 打印信息
    logger.info("=" * 60)
    logger.info("  Web Server Starting")
    logger.info("=" * 60)
    logger.info(f"  Mode: {'Mock (agents decoupled)' if USE_MOCK_AGENTS else 'Real agents'}")
    logger.info(f"  Host: {host}")
    logger.info(f"  Port: {port}")
    logger.info(f"  Debug: {debug}")
    logger.info("=" * 60)
    logger.info("  Available endpoints:")
    logger.info("    GET  /                      - Homepage")
    logger.info("    GET  /api/health           - Health check")
    logger.info("    POST /api/chat             - Chat with agent")
    logger.info("    POST /api/upload/pdf       - Upload PDF")
    logger.info("    POST /api/upload/image     - Upload image")
    logger.info("    GET  /api/questions        - List questions")
    logger.info("    GET  /api/questions/search - Search questions")
    logger.info("    GET  /api/questions/stats  - Question stats")
    logger.info("=" * 60)
    
    # 运行应用
    run_app(app, host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
