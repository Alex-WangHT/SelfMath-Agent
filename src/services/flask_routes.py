"""
Flask路由实现（Web表现层）

这是 Web 表现层的核心，处理所有 HTTP 请求。
只依赖桥接器层（src/interface/），不依赖任何具体的 Agent 实现。

设计模式：桥接器模式
- Web 层只依赖桥接器（AgentService）
- 桥接器内部调用具体的 Agent 实现
- 可以通过配置切换 Mock/Real Agent
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

from src.interface import AgentService, UploadResult, get_service

logger = logging.getLogger(__name__)


def create_app(agent_service: Optional[AgentService] = None, use_mock: bool = True) -> Flask:
    """
    创建 Flask 应用
    
    Args:
        agent_service: 自定义的 Agent 服务（可选）
        use_mock: 是否使用 Mock Agent（默认 True）
    
    Returns:
        Flask: Flask 应用实例
    """
    project_root = Path(__file__).parent.parent.parent
    
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
        static_url_path="/static"
    )
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "math-learning-agent-secret-key-2024-dev")
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = "./data/uploads"
    app.config["TEMP_FOLDER"] = "./data/temp"
    
    CORS(app)
    
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["TEMP_FOLDER"]).mkdir(parents=True, exist_ok=True)
    
    if agent_service is None:
        agent_service = get_service(use_mock=use_mock)
    
    app.agent_service = agent_service
    
    logger.info(f"Flask app created with service type: {type(agent_service).__name__}")
    
    _register_routes(app)
    
    return app


def _register_routes(app: Flask):
    """注册所有路由"""
    
    service = app.agent_service
    
    def get_or_create_session() -> str:
        """获取或创建会话 ID"""
        if "session_id" not in session:
            session["session_id"] = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
        return session["session_id"]
    
    @app.route("/")
    def index():
        """主页"""
        return render_template("index.html")
    
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """健康检查"""
        agents_info = service.list_agents()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "mode": "mock",
            "agents_available": [a.agent_id for a in agents_info]
        })
    
    @app.route("/api/chat", methods=["POST"])
    def chat():
        """聊天接口"""
        try:
            data = request.get_json() or {}
            user_message = data.get("message", "")
            agent_type = data.get("agent_role", "auto")
            
            if not user_message.strip():
                return jsonify({"error": "Message cannot be empty"}), 400
            
            conversation_id = get_or_create_session()
            
            response = service.chat(
                message=user_message,
                agent_type=agent_type,
                conversation_id=conversation_id
            )
            
            return jsonify({
                "success": True,
                "response": response.content,
                "agent_role": response.agent_type,
                "metadata": response.metadata,
                "mode": "mock"
            })
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/upload/pdf", methods=["POST"])
    def upload_pdf():
        """上传 PDF"""
        try:
            if "file" not in request.files:
                return jsonify({"error": "No file part"}), 400
            
            file = request.files["file"]
            
            if file.filename == "":
                return jsonify({"error": "No selected file"}), 400
            
            if not file.filename.lower().endswith(".pdf"):
                return jsonify({"error": "Only PDF files are allowed"}), 400
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            safe_filename = f"{timestamp}_{Path(file.filename).stem}.pdf"
            save_path = Path(app.config["UPLOAD_FOLDER"]) / safe_filename
            
            file.save(str(save_path))
            logger.info(f"PDF uploaded: {save_path}")
            
            start_page = request.form.get("start_page", 1)
            end_page = request.form.get("end_page")
            
            if isinstance(start_page, str):
                start_page = int(start_page) if start_page.isdigit() else 1
            if isinstance(end_page, str) and end_page:
                end_page = int(end_page) if end_page.isdigit() else None
            
            result = service.process_pdf(
                file_path=str(save_path),
                options={
                    "start_page": start_page,
                    "end_page": end_page
                }
            )
            
            return jsonify({
                "success": result.success,
                "filename": result.filename,
                "original_filename": file.filename,
                "questions_extracted": result.questions_extracted,
                "extracted_count": result.questions_extracted,
                "cross_page_count": 0,
                "examples": sum(1 for q in result.questions if q.question_type == "example"),
                "exercises": sum(1 for q in result.questions if q.question_type == "exercise"),
                "with_solution": 0,
                "questions": [q.to_dict() for q in result.questions[:10]],
                "mode": "mock",
                **result.metadata
            })
            
        except Exception as e:
            logger.error(f"PDF upload error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/upload/image", methods=["POST"])
    def upload_image():
        """上传图片"""
        try:
            if "file" not in request.files:
                return jsonify({"error": "No file part"}), 400
            
            file = request.files["file"]
            
            if file.filename == "":
                return jsonify({"error": "No selected file"}), 400
            
            allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
            file_ext = Path(file.filename).suffix.lower()
            
            if file_ext not in allowed_extensions:
                return jsonify({"error": f"Only image files allowed: {allowed_extensions}"}), 400
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            safe_filename = f"{timestamp}_{Path(file.filename).stem}{file_ext}"
            save_path = Path(app.config["UPLOAD_FOLDER"]) / safe_filename
            
            file.save(str(save_path))
            logger.info(f"Image uploaded: {save_path}")
            
            result = service.process_image(
                file_path=str(save_path)
            )
            
            return jsonify({
                "success": result.success,
                "filename": result.filename,
                "original_filename": file.filename,
                "ocr_text": result.metadata.get("ocr_text", ""),
                "questions": [q.to_dict() for q in result.questions],
                "mode": "mock",
                **result.metadata
            })
            
        except Exception as e:
            logger.error(f"Image upload error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/questions", methods=["GET"])
    def get_questions():
        """获取题目列表"""
        try:
            question_type = request.args.get("type")
            limit = request.args.get("limit", 100, type=int)
            
            questions = service.get_all_questions(
                question_type=question_type,
                limit=limit
            )
            
            return jsonify({
                "success": True,
                "total": len(questions),
                "questions": [q.to_dict() for q in questions],
                "mode": "mock"
            })
            
        except Exception as e:
            logger.error(f"Get questions error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/questions/search", methods=["GET", "POST"])
    def search_questions():
        """搜索题目"""
        try:
            if request.method == "POST":
                data = request.get_json() or {}
                query = data.get("query", "")
                n_results = data.get("n_results", 10)
                question_type = data.get("type")
            else:
                query = request.args.get("q", "")
                n_results = request.args.get("limit", 10, type=int)
                question_type = request.args.get("type")
            
            if not query:
                return jsonify({"error": "Search query is required"}), 400
            
            results = service.search_questions(
                query=query,
                n_results=n_results,
                question_type=question_type
            )
            
            return jsonify({
                "success": True,
                "query": query,
                "total": len(results),
                "results": [q.to_dict() for q in results],
                "mode": "mock"
            })
            
        except Exception as e:
            logger.error(f"Search questions error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/questions/stats", methods=["GET"])
    def get_question_stats():
        """获取题库统计"""
        try:
            stats = service.get_question_stats()
            return jsonify({
                "success": True,
                "stats": stats.to_dict(),
                "mode": "mock"
            })
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/conversation", methods=["GET"])
    def get_conversation():
        """获取对话历史"""
        try:
            conversation_id = get_or_create_session()
            conversation = service.get_conversation(conversation_id)
            
            if conversation:
                messages = [
                    {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                    for m in conversation.messages
                ]
            else:
                messages = []
            
            return jsonify({
                "success": True,
                "session_id": conversation_id,
                "history": messages
            })
            
        except Exception as e:
            logger.error(f"Get conversation error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/conversation/clear", methods=["POST"])
    def clear_conversation():
        """清除对话"""
        try:
            conversation_id = get_or_create_session()
            success = service.clear_conversation(conversation_id)
            
            return jsonify({
                "success": success,
                "message": "Conversation cleared" if success else "Conversation not found",
                "session_id": conversation_id
            })
            
        except Exception as e:
            logger.error(f"Clear conversation error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/agents", methods=["GET"])
    def list_agents():
        """列出可用 Agent"""
        try:
            agents_info = service.list_agents()
            return jsonify({
                "success": True,
                "agents": [a.to_dict() for a in agents_info],
                "mode": "mock"
            })
        except Exception as e:
            logger.error(f"List agents error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/mode", methods=["GET"])
    def get_mode():
        """获取当前模式"""
        return jsonify({
            "success": True,
            "mode": "mock",
            "message": "Current mode: Mock (agents decoupled)"
        })
    
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large. Maximum size is 100MB."}), 413
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500


def run_app(app: Flask, host: str = "0.0.0.0", port: int = 5000, debug: bool = True):
    """运行 Flask 应用"""
    logger.info("=" * 60)
    logger.info("  Math Learning Agent Web UI")
    logger.info("=" * 60)
    logger.info(f"  Host: {host}")
    logger.info(f"  Port: {port}")
    logger.info(f"  Debug: {debug}")
    logger.info("=" * 60)
    
    app.run(host=host, port=port, debug=debug)
