from flask import Blueprint, request, jsonify, current_app # type: ignore
from src.models import User, GraffitiReport, ReportPhoto
from src.util import get_db_session, get_file_url
from src.singleton import SingletonClass
from src.dadata_helper import normalize_address
from decouple import config # type: ignore
from geoalchemy2.shape import from_shape # type: ignore
from shapely.geometry import Point # type: ignore
import os

admin_bp = Blueprint('admin', __name__, template_folder='../templates')
singleton = SingletonClass()  # Fallback to in-memory if DB not available

@admin_bp.route('/api/debug', methods=['GET'])
def debug():
    """Debug endpoint to check database state"""
    # Check if DATABASE_URL is set
    if not os.environ.get('DATABASE_URL'):
        return jsonify({
            'total_applications': len(singleton.applications),
            'applications': singleton.applications,
            'database': 'Singleton (in-memory)'
        })

    try:
        with get_db_session() as session:
            total_reports = session.query(GraffitiReport).count()
            total_users = session.query(User).count()

            return jsonify({
                'total_applications': total_reports,
                'total_users': total_users,
                'database': 'PostgreSQL + PostGIS'
            })
    except Exception as e:
        current_app.logger.error(f"DB error in /api/debug: {e}")
        return jsonify(error=str(e)), 500

@admin_bp.route('/api/apply', methods=['POST'])
def apply():
    data = request.json
    if not data:
        return jsonify(success=False, error='No data provided'), 400

    # Fallback to Singleton if no DATABASE_URL
    if not os.environ.get('DATABASE_URL'):
        data['status'] = 'pending'
        singleton.applications.append(data)
        return jsonify(success=True, message='Application added successfully')

    try:
        with get_db_session() as session:
            # Получаем или создаём пользователя
            telegram_user_id = data.get('telegram_user_id')
            if not telegram_user_id:
                return jsonify(success=False, error='telegram_user_id is required'), 400

            user = session.query(User).filter_by(user_id=telegram_user_id).first()
            if not user:
                user = User(
                    user_id=telegram_user_id,
                    username=data.get('telegram_username'),
                    first_name=data.get('telegram_first_name'),
                    last_name=data.get('telegram_last_name')
                )
                session.add(user)
                session.flush()  # Получаем user_id

            # Нормализуем адрес через DaData (если адрес не содержит уже ФИАС)
            raw_address = data.get('raw_address')
            fias_id = data.get('fias_id')  # Может придти с фронта

            if not fias_id and raw_address:
                # Нормализуем через DaData API
                normalized_data = normalize_address(raw_address)
                normalized_addr = normalized_data.get('normalized_address')
                fias_id = normalized_data.get('fias_id')
                lat = normalized_data.get('latitude')
                lon = normalized_data.get('longitude')
            else:
                # Используем данные с фронта
                normalized_addr = raw_address
                lat = data.get('latitude')
                lon = data.get('longitude')

            # Создаём заявку
            report = GraffitiReport(
                user_id=user.user_id,
                normalized_address=normalized_addr or raw_address or '',
                fias_id=fias_id,
                description=data.get('comment') or data.get('description') or '',
                status='pending'
            )

            # Если есть координаты, добавляем location (PostGIS POINT)
            if lat is not None and lon is not None:
                point = Point(float(lon), float(lat))
                report.location = from_shape(point, srid=4326)

            session.add(report)
            # Context manager автоматически делает commit

            return jsonify(success=True, message='Application added successfully', report_id=report.report_id)
    except Exception as e:
        current_app.logger.error(f"Error in /api/apply: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(success=False, error=str(e)), 500

@admin_bp.route('/api/applications', methods=['GET'])
def get_applications():
    user_id = request.args.get('telegram_user_id', None)

    # Fallback to Singleton if no DATABASE_URL
    if not os.environ.get('DATABASE_URL'):
        if user_id:
            filtered_apps = [app for app in singleton.applications
                            if app.get('telegram_user_id') == int(user_id)]
            return jsonify(filtered_apps)
        return jsonify(singleton.applications)

    try:
        with get_db_session() as session:
            query = session.query(GraffitiReport).join(User)

            # Если user_id указан, фильтруем заявки только для этого пользователя
            if user_id:
                query = query.filter(User.user_id == int(user_id))

            reports = query.order_by(GraffitiReport.created_at.desc()).all()

            result = []
            for report in reports:
                # Получаем фото для этой заявки
                photos = session.query(ReportPhoto).filter_by(report_id=report.report_id).all()
                photo_urls = []
                for photo in photos:
                    try:
                        url = get_file_url(photo.s3_key)
                        if url:
                            photo_urls.append({
                                'id': photo.photo_id,
                                'url': url
                            })
                    except Exception as e:
                        current_app.logger.error(f"Error getting photo URL for {photo.s3_key}: {e}")

                result.append({
                    'id': report.report_id,
                    'location': report.normalized_address or '',
                    'comment': report.description or '',
                    'status': report.status,
                    'telegram_username': report.user.username,
                    'telegram_user_id': report.user.user_id,
                    'telegram_first_name': report.user.first_name,
                    'telegram_last_name': report.user.last_name,
                    'created_at': report.created_at.isoformat(),
                    'photos': photo_urls
                })

            return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in /api/applications: {e}")
        return jsonify(error=str(e)), 500

@admin_bp.route('/api/applications/moderate', methods=['POST'])
def moderate():
    data = request.json
    if not data:
        return jsonify(success=False, error='No data provided'), 400

    idx = int(data.get('idx'))
    new_status = data.get('status')
    password = data.get('admin_password')

    admin_password = config('ADMIN_PASSWORD', default='admin123')

    if password != admin_password:
        return jsonify(success=False, error='Invalid password'), 403

    # Fallback to Singleton if no DATABASE_URL
    if not os.environ.get('DATABASE_URL'):
        if 0 <= idx < len(singleton.applications):
            singleton.applications[idx]['status'] = new_status
            return jsonify(success=True, message='Status updated')
        else:
            return jsonify(success=False, error='Invalid index'), 400

    try:
        with get_db_session() as session:
            # idx is actually report_id from frontend
            report = session.query(GraffitiReport).filter_by(report_id=idx).first()
            if not report:
                return jsonify(success=False, error='Report not found'), 404

            report.status = new_status
            # Context manager автоматически делает commit

            return jsonify(success=True, message='Status updated')
    except Exception as e:
        current_app.logger.error(f"Error in /api/applications/moderate: {e}")
        return jsonify(success=False, error=str(e)), 500


@admin_bp.route('/api/upload/photo', methods=['POST'])
def upload_photo():
    """Upload photo to MinIO and attach to report."""
    from src.util import upload_file_to_s3
    from src.models import ReportPhoto
    import uuid

    if 'file' not in request.files:
        return jsonify(success=False, error='No file provided'), 400

    file = request.files['file']
    report_id = request.form.get('report_id')

    if not report_id:
        return jsonify(success=False, error='report_id is required'), 400

    if file.filename == '':
        return jsonify(success=False, error='Empty filename'), 400

    try:
        # Генерируем уникальное имя файла
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
        s3_key = f"photos/{report_id}/{uuid.uuid4()}.{ext}"

        # Загружаем в MinIO
        file_data = file.read()
        content_type = file.content_type or 'image/jpeg'

        uploaded_key = upload_file_to_s3(file_data, s3_key, content_type)

        if not uploaded_key:
            return jsonify(success=False, error='Failed to upload to storage'), 500

        # Если БД доступна, сохраняем запись
        if os.environ.get('DATABASE_URL'):
            with get_db_session() as session:
                photo = ReportPhoto(
                    report_id=int(report_id),
                    s3_key=uploaded_key
                )
                session.add(photo)
                # Context manager делает commit

        return jsonify(
            success=True,
            s3_key=uploaded_key,
            message='Photo uploaded successfully'
        )

    except Exception as e:
        current_app.logger.error(f"Error uploading photo: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(success=False, error=str(e)), 500


@admin_bp.route('/api/photo/<int:photo_id>', methods=['GET'])
def get_photo_url(photo_id):
    """Get presigned URL for photo download."""
    from src.util import get_file_url
    from src.models import ReportPhoto

    if not os.environ.get('DATABASE_URL'):
        return jsonify(error='Database not configured'), 500

    try:
        with get_db_session() as session:
            photo = session.query(ReportPhoto).filter_by(photo_id=photo_id).first()

            if not photo:
                return jsonify(error='Photo not found'), 404

            url = get_file_url(photo.s3_key, expires_in=3600)

            if not url:
                return jsonify(error='Failed to generate URL'), 500

            return jsonify(url=url, s3_key=photo.s3_key)

    except Exception as e:
        current_app.logger.error(f"Error getting photo URL: {e}")
        return jsonify(error=str(e)), 500


@admin_bp.route('/api/report/<int:report_id>/photos', methods=['GET'])
def get_report_photos(report_id):
    """Get all photo URLs for a report."""
    from src.util import get_file_url
    from src.models import ReportPhoto

    if not os.environ.get('DATABASE_URL'):
        return jsonify(error='Database not configured'), 500

    try:
        with get_db_session() as session:
            photos = session.query(ReportPhoto).filter_by(report_id=report_id).all()

            result = []
            for photo in photos:
                url = get_file_url(photo.s3_key, expires_in=3600)
                if url:
                    result.append({
                        'photo_id': photo.photo_id,
                        'url': url,
                        's3_key': photo.s3_key,
                        'uploaded_at': photo.uploaded_at.isoformat()
                    })

            return jsonify(photos=result)

    except Exception as e:
        current_app.logger.error(f"Error getting report photos: {e}")
        return jsonify(error=str(e)), 500
