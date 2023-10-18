import os
from flask import Flask
from models.common import DatabaseManager
from pathlib import Path
from dotenv import load_dotenv
from routes.dbController import db_route
# from routes.llmController import llm_route

app = Flask(__name__)

# Load environment variables
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DEBUG'] = os.getenv('DEBUG')
app.config['DB_URL'] = os.getenv('DB_URL')
app.config['DB_NAME'] = os.getenv('DB_NAME')
app.config['UPLOADS_PATH'] = Path(os.getenv('UPLOADS_PATH'))

# Configure Routes
app.register_blueprint(db_route, url_prefix='/db')
# app.register_blueprint(llm_route, url_prefix='/llm')

if __name__ == '__main__':
    app.run(port=8081,debug=app.config['DEBUG'])
    # db_manager = DatabaseManager(db_name=os.getenv('DB_NAME'), host=os.getenv('DB_URL'))
    # db_manager.connect()
    # db_name, host = get_db_config()
    # db_manager = DatabaseManager(db_name=db_name, host=host)
    # db_manager.connect()