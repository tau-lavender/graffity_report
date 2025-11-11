from flask import Blueprint, request, jsonify # type: ignore
from src.singleton import SingletonClass
from decouple import config # type: ignore

singleton = SingletonClass()
admin_bp = Blueprint('admin', __name__, template_folder='../templates')

@admin_bp.route('/api/debug', methods=['GET'])
def debug():
    """Debug endpoint to check singleton state"""
    return jsonify({
        'total_applications': len(singleton.applications),
        'applications': singleton.applications,
        'singleton_id': id(singleton)
    })

@admin_bp.route('/api/apply', methods=['POST'])
def apply():
    try:
        data = request.json
        if not data:
            return jsonify(success=False, error='No data provided'), 400

        data['status'] = 'pending'
        singleton.applications.append(data)
        return jsonify(success=True, message='Application added successfully')
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@admin_bp.route('/api/applications', methods=['GET'])
def get_applications():
    try:
        # Получаем telegram_user_id из параметров запроса
        user_id = request.args.get('telegram_user_id', None)

        # Если user_id указан, фильтруем заявки только для этого пользователя
        if user_id:
            filtered_apps = [app for app in singleton.applications
                            if app.get('telegram_user_id') == int(user_id)]
            return jsonify(filtered_apps)

        # Если user_id не указан, возвращаем все заявки
        return jsonify(singleton.applications)
    except Exception as e:
        return jsonify(error=str(e)), 500

@admin_bp.route('/api/applications/moderate', methods=['POST'])
def moderate():
    try:
        data = request.json
        if not data:
            return jsonify(success=False, error='No data provided'), 400

        idx = int(data.get('idx'))
        new_status = data.get('status')
        password = data.get('admin_password')

        admin_password = config('ADMIN_PASSWORD', default='admin123')

        if password != admin_password:
            return jsonify(success=False, error='Invalid password'), 403

        if 0 <= idx < len(singleton.applications):
            singleton.applications[idx]['status'] = new_status
            return jsonify(success=True, message='Status updated')
        else:
            return jsonify(success=False, error='Invalid index'), 400
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500
