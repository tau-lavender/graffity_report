from flask import Flask, jsonify  # type: ignore[import-not-found]
from werkzeug.exceptions import RequestEntityTooLarge  # type: ignore[import-not-found]
from sqlalchemy import text, inspect  # type: ignore[import-not-found]
from flask_cors import CORS  # type: ignore[import-untyped]
from src.app.admin import blueprints
from src.util import setup_database, init_minio, get_s3_client
from src.models import Base
import os


def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

    CORS(app,
         origins="*",
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=False)

    try:
        setup_database(app)
    except Exception as e:
        app.logger.warning(f"Database setup skipped: {e}")

    try:
        with app.app_context():
            init_minio()
    except Exception as e:
        app.logger.warning(f"MinIO setup skipped: {e}")

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_file(e):
        return jsonify(success=False, error="Размер файла превышает 25 МБ"), 413

    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify(success=False, error=str(e)), 400

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        return jsonify(success=False, error=str(e)), 500

    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'status': 'running',
            'service': 'GraffitiReport API'
        }), 200

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify(status='ok'), 200

    @app.route('/api/db/health', methods=['GET'])
    def db_health():
        engine = app.config.get("DB_ENGINE")
        if not engine:
            return jsonify(ok=False, error="DATABASE_URL is not set"), 200
        try:
            with engine.connect() as conn:
                pg_version = conn.execute(text("SELECT version()"))
                pgv = pg_version.scalar_one()
                try:
                    postgis_version = conn.execute(text("SELECT PostGIS_Version()"))
                    pgv_gis = postgis_version.scalar_one()
                except Exception:
                    pgv_gis = None
            return jsonify(ok=True, postgres=str(pgv), postgis=str(pgv_gis) if pgv_gis else None), 200
        except Exception as e:
            return jsonify(ok=False, error=str(e)), 200

    @app.route('/api/storage/health', methods=['GET'])
    def storage_health():
        endpoint = os.environ.get('MINIO_ENDPOINT')
        if not endpoint:
            return jsonify(ok=False, error="MINIO_ENDPOINT not set"), 200

        try:
            s3 = get_s3_client()
            if not s3:
                return jsonify(ok=False, error="S3 client not initialized"), 200

            bucket = os.environ.get('MINIO_BUCKET', 'graffiti-reports')
            buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]

            return jsonify(
                ok=True,
                endpoint=endpoint,
                bucket=bucket,
                bucket_exists=bucket in buckets
            ), 200
        except Exception as e:
            return jsonify(ok=False, error=str(e)), 200

    @app.route('/api/db/init', methods=['POST'])
    def init_db_tables():
        engine = app.config.get("DB_ENGINE")
        if not engine:
            return jsonify(ok=False, error="DATABASE_URL is not set"), 400

        try:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            Base.metadata.create_all(engine)

            new_inspector = inspect(engine)
            new_tables = new_inspector.get_table_names()

            return jsonify(
                ok=True,
                message="Tables initialized",
                existing_tables=existing_tables,
                all_tables=new_tables,
                created=list(set(new_tables) - set(existing_tables))
            ), 200
        except Exception as e:
            return jsonify(ok=False, error=str(e)), 500

    @app.route('/api/config', methods=['GET'])
    def get_config():
        return jsonify({
            'yandex_maps_api_key': os.environ.get('YANDEX_MAPS_API_KEY', '')
        }), 200

    return app
