from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from services.db_service import get_db
from utils.auth_utils import hash_password, verify_password

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'message': 'Name, email and password are required'}), 400

    users = get_db()['users']
    if users.find_one({'email': email}):
        return jsonify({'message': 'Email already exists'}), 409

    users.insert_one({
        'name': name,
        'email': email,
        'password_hash': hash_password(password),
        'created_at': datetime.utcnow(),
    })

    return jsonify({'message': 'User registered successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    users = get_db()['users']
    user = users.find_one({'email': email})

    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'message': 'Invalid email or password'}), 401

    token = create_access_token(identity=str(user['_id']))

    return jsonify({
        'access_token': token,
        'user': {
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email'],
        }
    })
