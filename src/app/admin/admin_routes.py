from flask import Blueprint, request, jsonify, current_app # type: ignore
from src.models import User, GraffitiReport
from src.util import get_db_session
from decouple import config # type: ignore
from geoalchemy2.shape import from_shape # type: ignore
from shapely.geometry import Point # type: ignore

admin_bp = Blueprint('admin', __name__, template_folder='../templates')

@admin_bp.route('/api/debug', methods=['GET'])
def debug():
    """Debug endpoint to check database state"""
    session = get_db_session()
    try:
        total_reports = session.query(GraffitiReport).count()
        total_users = session.query(User).count()

        return jsonify({
            'total_applications': total_reports,
            'total_users': total_users,
            'database': 'PostgreSQL + PostGIS'
        })
    except Exception as e:
        return jsonify(error=str(e)), 500
    finally:
        session.close()

@admin_bp.route('/api/apply', methods=['POST'])
def apply():
    session = get_db_session()
    try:
        data = request.json
        if not data:
            return jsonify(success=False, error='No data provided'), 400

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

        # Создаём заявку
        report = GraffitiReport(
            user_id=user.user_id,
            address=data.get('location'),
            comment=data.get('comment'),
            status='pending'
        )

        # Если есть координаты, добавляем location
        lat = data.get('latitude')
        lon = data.get('longitude')
        if lat is not None and lon is not None:
            point = Point(float(lon), float(lat))
            report.location = from_shape(point, srid=4326)

        session.add(report)
        session.commit()

        return jsonify(success=True, message='Application added successfully', report_id=report.report_id)
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error in /api/apply: {e}")
        return jsonify(success=False, error=str(e)), 500
    finally:
        session.close()

@admin_bp.route('/api/applications', methods=['GET'])
def get_applications():
    session = get_db_session()
    try:
        # Получаем telegram_user_id из параметров запроса
        user_id = request.args.get('telegram_user_id', None)

        query = session.query(GraffitiReport).join(User)

        # Если user_id указан, фильтруем заявки только для этого пользователя
        if user_id:
            query = query.filter(User.user_id == int(user_id))

        reports = query.order_by(GraffitiReport.created_at.desc()).all()

        result = []
        for report in reports:
            result.append({
                'id': report.report_id,
                'location': report.address,
                'comment': report.comment,
                'status': report.status,
                'telegram_username': report.user.username,
                'telegram_user_id': report.user.user_id,
                'telegram_first_name': report.user.first_name,
                'telegram_last_name': report.user.last_name,
                'created_at': report.created_at.isoformat()
            })

        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in /api/applications: {e}")
        return jsonify(error=str(e)), 500
    finally:
        session.close()

@admin_bp.route('/api/applications/moderate', methods=['POST'])
def moderate():
    session = get_db_session()
    try:
        data = request.json
        if not data:
            return jsonify(success=False, error='No data provided'), 400

        report_id = int(data.get('idx'))  # Фронт передаёт idx, но это report_id
        new_status = data.get('status')
        password = data.get('admin_password')

        admin_password = config('ADMIN_PASSWORD', default='admin123')

        if password != admin_password:
            return jsonify(success=False, error='Invalid password'), 403

        report = session.query(GraffitiReport).filter_by(report_id=report_id).first()
        if not report:
            return jsonify(success=False, error='Report not found'), 404

        report.status = new_status
        session.commit()

        return jsonify(success=True, message='Status updated')
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error in /api/applications/moderate: {e}")
        return jsonify(success=False, error=str(e)), 500
    finally:
        session.close()
