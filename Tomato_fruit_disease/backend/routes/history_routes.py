from datetime import datetime

from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.db_service import get_db

history_bp = Blueprint('history', __name__)


@history_bp.route('/history', methods=['GET'])
@jwt_required()
def list_history():
    user_id = get_jwt_identity()
    records = (
        get_db()['fruit_history']
        .find({'user_id': ObjectId(user_id)})
        .sort('created_at', -1)
    )

    payload = []
    for item in records:
        payload.append({
            '_id': str(item['_id']),
            'class_name': item['class_name'],
            'confidence': item['confidence'],
            'warning': item.get('warning', ''),
            'description': item.get('description', ''),
            'symptoms': item.get('symptoms', ''),
            'solution': item.get('solution', ''),
            'treatment': item.get('treatment', ''),
            'image_uri': item.get('image_uri'),
            'created_at': item['created_at'].isoformat(),
        })

    return jsonify({'history': payload})


@history_bp.route('/history', methods=['POST'])
@jwt_required()
def create_history():
    user_id = get_jwt_identity()
    data = request.get_json(force=True)

    entry = {
        'user_id': ObjectId(user_id),
        'class_name': data.get('class'),
        'confidence': float(data.get('confidence', 0)),
        'warning': data.get('warning', ''),
        'description': data.get('description', ''),
        'symptoms': data.get('symptoms', ''),
        'solution': data.get('solution', ''),
        'treatment': data.get('treatment', ''),
        'image_uri': data.get('image_uri'),
        'created_at': datetime.utcnow(),
    }

    result = get_db()['fruit_history'].insert_one(entry)
    return jsonify({'message': 'Saved', 'id': str(result.inserted_id)}), 201

