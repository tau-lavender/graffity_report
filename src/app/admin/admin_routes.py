from flask import Blueprint, request, jsonify, current_app, send_file
from geoalchemy2.shape import to_shape, from_shape
from src.models import User, GraffitiReport, ReportPhoto
from src.util import get_db_session, get_file_from_s3, upload_file_to_s3, get_file_url
from src.singleton import SingletonClass
from src.dadata_helper import normalize_address
from decouple import config
from shapely.geometry import Point
import os
import io
import uuid

admin_bp = Blueprint('admin', __name__, template_folder='../templates')
singleton = SingletonClass()

@admin_bp.route('/api/debug', methods=['GET'])
def debug():
    if not os.environ.get('DATABASE_URL'):
        return jsonify({
            'total_applications': len(singleton.applications),
            'applications': singleton.applications,
            'database': 'Singleton'
        })

    try:
        with get_db_session() as session:
            total_reports = session.query(GraffitiReport).count()
            total_users = session.query(User).count()

            return jsonify({
                'total_applications': total_reports,
                'total_users': total_users,
                'database': 'PostgreSQL'
            })
    except Exception as e:
        current_app.logger.error(f"DB error: {e}")
        return jsonify(error=str(e)), 500

@admin_bp.route('/api/apply', methods=['POST'])
def apply():
    data = request.json
    if not data:
        return jsonify(success=False, error='No data provided'), 400

    if not os.environ.get('DATABASE_URL'):
        report_id = singleton.next_report_id()
        item = {
            'id': report_id,
            'report_id': report_id,
            'location': data.get('raw_address') or data.get('normalized_address') or '',
            'comment': data.get('comment') or data.get('description') or '',
            'status': 'pending',
            'telegram_username': data.get('telegram_username'),
            'telegram_user_id': data.get('telegram_user_id'),
            'telegram_first_name': data.get('telegram_first_name'),
            'telegram_last_name': data.get('telegram_last_name'),
            'created_at': None
        }
        singleton.applications.append(item)
        singleton.photos[report_id] = []
        return jsonify(success=True, message='Application added', report_id=report_id)

    try:
        with get_db_session() as session:
            telegram_user_id = data.get('telegram_user_id')
            user = None

            if telegram_user_id:
                user = session.query(User).filter_by(user_id=telegram_user_id).first()
                if not user:
                    user = User(
                        user_id=telegram_user_id,
                        username=data.get('telegram_username'),
                        first_name=data.get('telegram_first_name'),
                        last_name=data.get('telegram_last_name')
                    )
                    session.add(user)
                    session.flush()

            raw_address = data.get('raw_address')
            fias_id = data.get('fias_id')

            if not fias_id and raw_address:
                normalized_data = normalize_address(raw_address)
                normalized_addr = normalized_data.get('normalized_address')
                fias_id = normalized_data.get('fias_id')
                lat = normalized_data.get('latitude')
                lon = normalized_data.get('longitude')
            else:
                normalized_addr = raw_address
                lat = data.get('latitude')
                lon = data.get('longitude')

            report = GraffitiReport(
                user_id=user.user_id if user else None,
                normalized_address=normalized_addr or raw_address or '',
                fias_id=fias_id,
                description=data.get('comment') or data.get('description') or '',
                status='pending'
            )

            if lat is not None and lon is not None:
                point = Point(float(lon), float(lat))
                report.location = from_shape(point, srid=4326)

            session.add(report)
            session.flush()

            return jsonify(success=True, message='Application added', report_id=report.report_id)
    except Exception as e:
        current_app.logger.error(f"Error in /api/apply: {e}")
        return jsonify(success=False, error=str(e)), 500

@admin_bp.route('/api/applications', methods=['GET'])
def get_applications():
    user_id = request.args.get('telegram_user_id', None)

    if not os.environ.get('DATABASE_URL'):
        apps = []
        for app in singleton.applications:
            if user_id and app.get('telegram_user_id') != int(user_id):
                continue
            rid = app.get('report_id') or app.get('id')
            photos = singleton.photos.get(rid, [])
            app_copy = app.copy()
            app_copy['photos'] = [{'id': p.get('id'), 'url': p.get('url') or p.get('s3_key')} for p in photos]
            apps.append(app_copy)
        return jsonify(apps)

    try:
        with get_db_session() as session:
            query = session.query(GraffitiReport).outerjoin(User)

            if user_id:
                query = query.filter(User.user_id == int(user_id))

            reports = query.order_by(GraffitiReport.created_at.desc()).all()

            result = []
            for report in reports:
                photos = session.query(ReportPhoto).filter_by(report_id=report.report_id).all()
                photo_urls = []
                for photo in photos:
                    photo_urls.append({
                        'id': photo.photo_id,
                        'url': f'/api/photo/download/{photo.photo_id}',
                        's3_key': photo.s3_key
                    })

                latitude = None
                longitude = None
                if report.location is not None:
                    try:
                        shape = to_shape(report.location)
                        longitude = shape.x
                        latitude = shape.y
                    except Exception as e:
                        current_app.logger.warning(f"Failed to extract coordinates: {e}")

                result.append({
                    'report_id': report.report_id,
                    'normalized_address': report.normalized_address or '',
                    'description': report.description or '',
                    'status': report.status,
                    'telegram_username': report.user.username if report.user else None,
                    'telegram_user_id': report.user.user_id if report.user else None,
                    'telegram_first_name': report.user.first_name if report.user else None,
                    'telegram_last_name': report.user.last_name if report.user else None,
                    'created_at': report.created_at.isoformat(),
                    'fias_id': str(report.fias_id) if report.fias_id else None,
                    'latitude': latitude,
                    'longitude': longitude,
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

    if not os.environ.get('DATABASE_URL'):
        if 0 <= idx < len(singleton.applications):
            singleton.applications[idx]['status'] = new_status
            return jsonify(success=True, message='Status updated')
        else:
            return jsonify(success=False, error='Invalid index'), 400

    try:
        with get_db_session() as session:
            report = session.query(GraffitiReport).filter_by(report_id=idx).first()
            if not report:
                return jsonify(success=False, error='Report not found'), 404

            report.status = new_status

            return jsonify(success=True, message='Status updated')
    except Exception as e:
        current_app.logger.error(f"Error in /api/applications/moderate: {e}")
        return jsonify(success=False, error=str(e)), 500


@admin_bp.route('/api/upload/photo', methods=['POST'])
def upload_photo():
    if 'file' not in request.files:
        return jsonify(success=False, error='No file provided'), 400

    file = request.files['file']
    report_id = request.form.get('report_id')

    if not report_id:
        return jsonify(success=False, error='report_id is required'), 400

    if not file.filename:
        return jsonify(success=False, error='Empty filename'), 400

    try:
        file_data = file.read()
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
        s3_key = f"photos/{report_id}/{uuid.uuid4()}.{ext}"
        content_type = file.content_type or 'image/jpeg'

        upload_file_to_s3(file_data, s3_key, content_type)

        with get_db_session() as session:
            photo = ReportPhoto(
                report_id=int(report_id),
                s3_key=s3_key
            )
            session.add(photo)
            session.flush()

        return jsonify(success=True, s3_key=s3_key)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@admin_bp.route('/api/photos/all', methods=['GET'])
def get_all_photos():
    if not os.environ.get('DATABASE_URL'):
        result = []
        for report_id, photos in singleton.photos.items():
            for photo in photos:
                result.append({
                    'photo_id': photo.get('id'),
                    'report_id': report_id,
                    's3_key': photo.get('s3_key'),
                    'url': photo.get('url')
                })
        return jsonify(total=len(result), photos=result)

    try:
        with get_db_session() as session:
            photos = session.query(ReportPhoto).all()

            result = []
            for photo in photos:
                result.append({
                    'photo_id': photo.photo_id,
                    'report_id': photo.report_id,
                    's3_key': photo.s3_key,
                    'uploaded_at': photo.uploaded_at.isoformat() if photo.uploaded_at else None
                })

            return jsonify(total=len(result), photos=result)
    except Exception as e:
        current_app.logger.error(f"Error getting all photos: {e}")
        return jsonify(error=str(e)), 500


@admin_bp.route('/api/photo/<int:photo_id>', methods=['GET'])
def get_photo_url(photo_id):
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


@admin_bp.route('/api/photo/download/<int:photo_id>', methods=['GET'])
def download_photo(photo_id):
    if not os.environ.get('DATABASE_URL'):
        return jsonify(error='Database not configured'), 500

    try:
        with get_db_session() as session:
            photo = session.query(ReportPhoto).filter_by(photo_id=photo_id).first()

            if not photo:
                return jsonify(error='Photo not found'), 404

            file_bytes = get_file_from_s3(photo.s3_key)

            if not file_bytes:
                return jsonify(error='Failed to download file from storage'), 500

            ext = photo.s3_key.rsplit('.', 1)[-1].lower() if '.' in photo.s3_key else 'jpg'
            mime_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')

            return send_file(
                io.BytesIO(file_bytes),
                mimetype=mime_type,
                as_attachment=False,
                download_name=f'photo_{photo_id}.{ext}'
            )

    except Exception as e:
        current_app.logger.error(f"Error downloading photo: {e}")
        return jsonify(error=str(e)), 500


@admin_bp.route('/api/report/<int:report_id>/photos', methods=['GET'])
def get_report_photos(report_id):
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
