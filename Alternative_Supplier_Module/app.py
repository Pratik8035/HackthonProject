from flask import Flask
from routes.supplier_api import supplier_bp
from routes.analysis_api import analysis_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(supplier_bp)
app.register_blueprint(analysis_bp)

@app.route('/')
def home():
    return "Supply Chain Risk Management Dashboard Backend is Running!"

if __name__ == '__main__':
    # Run the application
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
