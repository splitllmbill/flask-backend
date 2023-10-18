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


#    db_manager.insert_document(User, username="jane_doe", email="jane@example.com", age=25)

    # Find all users
    # all_users = db_manager.find_documents(User)

    # Find a user with a specific username
    # john_doe = db_manager.find_document(User, query={"username": "john_doe"})

    # Update a user
    # if john_doe:
    #     db_manager.update_document(john_doe, age=31)

   #Find a user you want to delete
    # user_to_delete = db_manager.find_document(User, query={"username": "john_doe"})

    # if user_to_delete:
    #     # Delete the user
    #     db_manager.delete_document(user_to_delete)
