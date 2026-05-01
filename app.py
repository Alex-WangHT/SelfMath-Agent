import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USE_MOCK_AGENTS = os.getenv("USE_MOCK_AGENTS", "True").lower() == "true"

try:
    if USE_MOCK_AGENTS:
        from src.agents.mock_agent_manager import get_agent_manager
    else:
        from src.agents.mock_agent_manager import get_agent_manager
except ImportError as e:
    logger.warning(f"Failed to import agent manager: {e}, using fallback")
    from src.agents.mock_agent_manager import get_agent_manager

try:
    from src.agents.base_agent import AgentRole
    HAS_AGENT_ROLE = True
except ImportError:
    HAS_AGENT_ROLE = False
    logger.warning("AgentRole not available, using string roles")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "math-learning-agent-secret-key-2024-dev")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = "./data/uploads"
app.config["TEMP_FOLDER"] = "./data/temp"

CORS(app)

Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
Path(app.config["TEMP_FOLDER"]).mkdir(parents=True, exist_ok=True)

agent_manager = get_agent_manager(use_mock=USE_MOCK_AGENTS)

logger.info(f"Agent Manager initialized: {'Mock Mode' if USE_MOCK_AGENTS else 'Real Mode'}")


def get_or_create_session() -> str:
    if "session_id" not in session:
        session["session_id"] = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
        session["conversation_history"] = []
    return session["session_id"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    agents_info = []
    if hasattr(agent_manager, 'list_agents'):
        agents_info = agent_manager.list_agents()
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mode": "mock" if USE_MOCK_AGENTS else "real",
        "agents_available": [a.get("role", "unknown") for a in agents_info]
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        agent_role = data.get("agent_role", "question_bank")
        
        if not user_message.strip():
            return jsonify({"error": "Message cannot be empty"}), 400
        
        session_id = get_or_create_session()
        
        if "conversation_history" not in session:
            session["conversation_history"] = []
        
        session["conversation_history"].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        role_enum = None
        if HAS_AGENT_ROLE:
            try:
                role_enum = AgentRole(agent_role) if agent_role in [r.value for r in AgentRole] else None
            except ValueError:
                role_enum = None
        
        response = agent_manager.chat(
            user_message=user_message,
            agent_role=role_enum if role_enum else agent_role,
            session_id=session_id,
            context=session.get("conversation_history", [])
        )
        
        session["conversation_history"].append({
            "role": "assistant",
            "content": response.get("content", ""),
            "agent_role": response.get("agent_role", agent_role),
            "timestamp": datetime.now().isoformat()
        })
        
        session.modified = True
        
        return jsonify({
            "success": True,
            "response": response.get("content", ""),
            "agent_role": response.get("agent_role", agent_role),
            "metadata": response.get("metadata", {}),
            "mode": "mock" if USE_MOCK_AGENTS else "real"
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload/pdf", methods=["POST"])
def upload_pdf():
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
        
        session_id = get_or_create_session()
        
        start_page = request.form.get("start_page", 0)
        end_page = request.form.get("end_page", None)
        
        if isinstance(start_page, str):
            start_page = int(start_page) if start_page.isdigit() else 0
        if isinstance(end_page, str) and end_page:
            end_page = int(end_page) if end_page.isdigit() else None
        
        result = agent_manager.process_pdf(
            pdf_path=str(save_path),
            start_page=start_page,
            end_page=end_page,
            session_id=session_id
        )
        
        return jsonify({
            "success": True,
            "filename": safe_filename,
            "original_filename": file.filename,
            "questions_extracted": result.get("total_questions", 0),
            "extracted_count": result.get("extracted_count", result.get("total_questions", 0)),
            "cross_page_count": result.get("cross_page_count", 0),
            "examples": result.get("example_count", 0),
            "exercises": result.get("exercise_count", 0),
            "with_solution": result.get("with_solution_count", 0),
            "questions": result.get("questions", [])[:10],
            "mode": "mock" if USE_MOCK_AGENTS else "real"
        })
        
    except Exception as e:
        logger.error(f"PDF upload error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload/image", methods=["POST"])
def upload_image():
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
        
        session_id = get_or_create_session()
        
        result = agent_manager.process_image(
            image_path=str(save_path),
            session_id=session_id
        )
        
        return jsonify({
            "success": True,
            "filename": safe_filename,
            "original_filename": file.filename,
            "ocr_text": result.get("ocr_text", ""),
            "questions": result.get("questions", []),
            "mode": "mock" if USE_MOCK_AGENTS else "real"
        })
        
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/questions", methods=["GET"])
def get_questions():
    try:
        question_type = request.args.get("type")
        limit = request.args.get("limit", 100, type=int)
        
        questions = agent_manager.get_all_questions(question_type=question_type)
        
        if limit:
            questions = questions[:limit]
        
        return jsonify({
            "success": True,
            "total": len(questions),
            "questions": questions,
            "mode": "mock" if USE_MOCK_AGENTS else "real"
        })
        
    except Exception as e:
        logger.error(f"Get questions error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/questions/search", methods=["GET", "POST"])
def search_questions():
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            query = data.get("query", "")
            n_results = data.get("n_results", 5)
            question_type = data.get("type")
        else:
            query = request.args.get("q", "")
            n_results = request.args.get("limit", 5, type=int)
            question_type = request.args.get("type")
        
        if not query:
            return jsonify({"error": "Search query is required"}), 400
        
        results = agent_manager.search_questions(
            query=query,
            n_results=n_results,
            question_type=question_type
        )
        
        return jsonify({
            "success": True,
            "query": query,
            "total": len(results),
            "results": results,
            "mode": "mock" if USE_MOCK_AGENTS else "real"
        })
        
    except Exception as e:
        logger.error(f"Search questions error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/questions/stats", methods=["GET"])
def get_question_stats():
    try:
        stats = agent_manager.get_question_stats()
        return jsonify({
            "success": True,
            "stats": stats,
            "mode": "mock" if USE_MOCK_AGENTS else "real"
        })
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversation", methods=["GET"])
def get_conversation():
    try:
        session_id = get_or_create_session()
        history = session.get("conversation_history", [])
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "history": history
        })
        
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversation/clear", methods=["POST"])
def clear_conversation():
    try:
        session_id = get_or_create_session()
        session["conversation_history"] = []
        session.modified = True
        
        return jsonify({
            "success": True,
            "message": "Conversation cleared",
            "session_id": session_id
        })
        
    except Exception as e:
        logger.error(f"Clear conversation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/agents", methods=["GET"])
def list_agents():
    try:
        agents_info = agent_manager.list_agents()
        return jsonify({
            "success": True,
            "agents": agents_info,
            "mode": "mock" if USE_MOCK_AGENTS else "real"
        })
    except Exception as e:
        logger.error(f"List agents error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/mode", methods=["GET"])
def get_mode():
    return jsonify({
        "success": True,
        "mode": "mock" if USE_MOCK_AGENTS else "real",
        "message": "Current mode: " + ("Mock (agents decoupled)" if USE_MOCK_AGENTS else "Real agents")
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


def main():
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    logger.info("=" * 60)
    logger.info("  Math Learning Agent Web UI")
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
    
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
