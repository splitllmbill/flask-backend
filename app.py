import os
from flask import Flask
from pathlib import Path
from dotenv import load_dotenv
from routes.dbController import db_route
from routes.llmController import llm_route

app = Flask(__name__)

@app.after_request
def add_cache_control(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

# Load environment variables
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DB_URL'] = os.getenv('DB_URL')
app.config['DB_NAME'] = os.getenv('DB_NAME')
app.config['UPLOADS_PATH'] = Path(os.getenv('UPLOADS_PATH'))
app.config['LLM_API_KEY'] = os.getenv('LLM_API_KEY')
app.config['ADMIN_CODE'] = os.getenv('ADMIN_CODE')

# Configure Routes
app.register_blueprint(db_route, url_prefix='/db')
app.register_blueprint(llm_route, url_prefix='/llm')

if __name__ == '__main__':
    app.run(port=8081,host = '0.0.0.0',debug=True)