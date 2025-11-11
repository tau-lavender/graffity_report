from flask import Flask, jsonify  # type: ignore
from flask_cors import CORS  # type: ignore
from src.app.admin import blueprints


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Register all blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Simple health endpoint (useful for platform checks)
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify(status='ok'), 200

    return app
