from flask import Flask, jsonify, request  # type: ignore
from flask_cors import CORS  # type: ignore
from src.app.admin import blueprints


def create_app():
    app = Flask(__name__)

    # Configure CORS for ALL routes (not just /api/*)
    CORS(app,
         origins=[
             "https://tau-lavender.github.io",
             "http://localhost:8080",
             "http://0.0.0.0:8080"
         ],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=True)

    # Register all blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Root endpoint for quick check
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'status': 'running',
            'service': 'GraffitiReport API',
            'endpoints': {
                'health': '/health',
                'applications': '/api/applications',
                'apply': '/api/apply',
                'moderate': '/api/applications/moderate'
            }
        }), 200

    # Simple health endpoint (useful for platform checks)
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify(status='ok'), 200

    # Basic request logging to help diagnose 502/timeouts in production
    @app.before_request
    def _log_request():
        try:
            app.logger.info(f"REQ {request.method} {request.path} headers={dict(request.headers)}")
        except Exception:
            pass

    @app.after_request
    def _log_response(response):
        try:
            app.logger.info(f"RES {request.method} {request.path} status={response.status_code}")
        except Exception:
            pass
        return response

    return app
