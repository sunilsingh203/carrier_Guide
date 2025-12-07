from flask import Flask, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

print()
# Initialize Flask app with template and static folder paths
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Register blueprints
from routes.recommend import recommend_bp
app.register_blueprint(recommend_bp, url_prefix='/api')

@app.route('/')
def index():
    """Serve the main index page"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'active',
        'message': 'CareerHelper API is running',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)