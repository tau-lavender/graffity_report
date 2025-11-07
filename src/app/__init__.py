from flask import Flask # type: ignore
from src.app.admin import blueprints

def create_app():
    app = Flask(__name__)

    # Register all blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    return app
