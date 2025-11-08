from flask import Blueprint, request, jsonify # type: ignore
from src.singleton import SingletonClass
from decouple import config # type: ignore

singleton = SingletonClass()
admin_bp = Blueprint('admin', __name__, template_folder='../templates')

@admin_bp.route('/api/apply', methods=['POST'])
def apply():
    data = request.json
    data['status'] = 'pending'
    singleton.applications.append(data)
    return jsonify(success=True)

@admin_bp.route('/api/applications', methods=['GET'])
def get_applications():
    # Получаем telegram_user_id из параметров запроса
    user_id = request.args.get('telegram_user_id', None)
    
    # Если user_id указан, фильтруем заявки только для этого пользователя
    if user_id:
        filtered_apps = [app for app in singleton.applications 
                        if app.get('telegram_user_id') == int(user_id)]
        return jsonify(filtered_apps)
    
    # Если user_id не указан, возвращаем все заявки
    return jsonify(singleton.applications)

@admin_bp.route('/api/applications/moderate', methods=['POST'])
def moderate():
    idx = int(request.json['idx'])
    new_status = request.json['status']
    password = request.json['admin_password']
    if password == config('ADMIN_PASSWORD')  and 0 <= idx < len(singleton.applications):
        singleton.applications[idx]['status'] = new_status
        return jsonify(success=True)
    return jsonify(success=False)
