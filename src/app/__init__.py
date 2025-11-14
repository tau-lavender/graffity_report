from flask import Flask, jsonify, request  # type: ignore
from sqlalchemy import text  # type: ignore
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

    # Initialize database (if DATABASE_URL is set)
    try:
        from src.util import setup_database
        setup_database(app)
    except Exception as e:
        app.logger.warning(f"Database setup skipped: {e}")

    # Initialize MinIO storage
    try:
        from src.util import init_minio
        with app.app_context():
            init_minio()
    except Exception as e:
        app.logger.warning(f"MinIO setup skipped: {e}")

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

    # Database health endpoint (verifies connection and PostGIS availability)
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

    # MinIO/S3 storage health endpoint
    @app.route('/api/storage/health', methods=['GET'])
    def storage_health():
        import os
        from src.util import get_s3_client

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
                bucket_exists=bucket in buckets,
                all_buckets=buckets
            ), 200
        except Exception as e:
            return jsonify(ok=False, error=str(e)), 200

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
