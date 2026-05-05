from flask import Blueprint, jsonify, request
from services.model_service import predict_image

predict_bp = Blueprint('predict', __name__)


@predict_bp.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        result = predict_image(file.stream)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
