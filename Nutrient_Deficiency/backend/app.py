import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from services.db_service import init_db
from services.model_service import class_names
from routes.predict_routes import predict_bp
from routes.auth_routes import auth_bp
from routes.history_routes import history_bp
from routes.stats_routes import stats_bp

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

JWTManager(app)
init_db()

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(predict_bp)
app.register_blueprint(history_bp)
app.register_blueprint(stats_bp)


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Tomato Leaf Nutrient Deficiency API',
        'status': 'running',
        'classes': class_names
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
