from flask import Flask, request, jsonify

app = Flask(__name__)
applications = []
admin_password = "1234"

@app.route('/api/apply', methods=['POST'])
def apply():
    data = request.json
    data['status'] = 'pending'
    applications.append(data)
    return jsonify(success=True)

@app.route('/api/my_applications')
def my_applications():
    tg_id = request.args.get('tg_id')
    if not tg_id:
        return jsonify([])
    user_apps = [a for a in applications if str(a.get('tg_id')) == tg_id]
    return jsonify(user_apps)


@app.route('/api/applications', methods=['GET'])
def get_applications():
    return jsonify(applications)

@app.route('/api/applications/moderate', methods=['POST'])
def moderate():
    idx = int(request.json['idx'])
    new_status = request.json['status']
    password = request.json['admin_password']
    if password == admin_password and 0 <= idx < len(applications):
        applications[idx]['status'] = new_status
        return jsonify(success=True)
    return jsonify(success=False)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
