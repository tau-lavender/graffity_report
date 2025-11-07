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
