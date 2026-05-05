from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson import ObjectId
from services.db_service import get_db

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = get_jwt_identity()
    history_collection = get_db()['history']

    records = list(history_collection.find({'user_id': ObjectId(user_id)}))

    class_counts = {}
    scans_by_day = {}

    for item in records:
        cls = item.get('class_name', 'Unknown')
        class_counts[cls] = class_counts.get(cls, 0) + 1

        day = item.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d')
        scans_by_day[day] = scans_by_day.get(day, 0) + 1

    most_common = 'N/A'
    if class_counts:
        most_common = max(class_counts, key=class_counts.get)

    timeline = []
    for i in range(6, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        timeline.append({'date': day, 'count': scans_by_day.get(day, 0)})

    return jsonify({
        'total_scans': len(records),
        'most_common_deficiency': most_common,
        'class_counts': class_counts,
        'scans_per_day': timeline,
    })
