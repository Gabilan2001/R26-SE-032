from flask import jsonify


def ok(data=None, message='ok', status=200):
    payload = {'message': message}
    if data is not None:
        payload['data'] = data
    return jsonify(payload), status


def fail(message='error', status=400):
    return jsonify({'message': message}), status

