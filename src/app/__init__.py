from flask import Flask, send_from_directory # type: ignore
from flask_cors import CORS # type: ignore
from src.app.admin import blueprints
import os

def create_app():
    app = Flask(__name__, static_folder='static')
    CORS(app)

    # Register all blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    @app.route('/docs/<path:filename>')
    def serve_docs(filename):
        docs_path = os.path.join(app.static_folder, 'docs')
        return send_from_directory(docs_path, filename)

    @app.route('/')
    def index():
        return send_from_directory(os.path.join(app.static_folder, 'docs'), 'index.html')

    return app
