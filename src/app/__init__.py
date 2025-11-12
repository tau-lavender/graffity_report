from flask import Flask, jsonify  # type: ignore
from flask_cors import CORS  # type: ignore
from src.app.admin import blueprints


def create_app():
    app = Flask(__name__)

    # Configure CORS to allow GitHub Pages
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://tau-lavender.github.io",
                "http://localhost:8080",
                "http://127.0.0.1:8080"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

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

    return app
