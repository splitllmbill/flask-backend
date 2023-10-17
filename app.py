import os
from flask import Flask, Response, request, jsonify
# import easyocr
import uuid
from mongoengine import connect
import models.common as models

# reader = easyocr.Reader(['en'])

app = Flask(__name__)

# Set the upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'


#connect(db='dummy', host='mongodb+srv://username:password@cluster0.tcjo5lg.mongodb.net/?retryWrites=true&w=majority')
# Function to check if the folder for uploads exists, and create it if not
def create_upload_folder():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

def generate_unique_filename(filename):
    # Generate a unique filename using a combination of timestamp and a random string
    unique_filename = str(uuid.uuid4()) + '_' + filename
    return unique_filename

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No selected file'})

        create_upload_folder()

        # Generate a unique filename for the uploaded file
        unique_filename = generate_unique_filename(file.filename)

        # Save the uploaded file using the unique filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

        
        #result = reader.readtext(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename),detail=0)

        return jsonify({'message': 'File uploaded successfully', 'filename': unique_filename, 'ocr': "success"})
    
@app.route('/expense', methods=['POST'])
def calculate_expense():
    if request.method == 'POST':
        data = request.get_json() 
        sentence = data.get('requestData', 0)['sentence']

        response = {
            'responseData': sentence
        }

        return jsonify(response)
    

@app.route('/noob', methods=['POST'])
def noob():
    if request.method == 'POST':
        data = request.get_json() 

        users =models.User.objects
        r = Response(response=users.to_json(), status=200, mimetype="application/json")
    return r

if __name__ == '__main__':
    app.run(port=8081,debug=True)
    db_manager = models.DatabaseManager()

#    db_manager.insert_document(User, username="jane_doe", email="jane@example.com", age=25)

#     # Find all users
#     all_users = db_manager.find_documents(User)

#     # Find a user with a specific username
#     john_doe = db_manager.find_document(User, query={"username": "john_doe"})

#     # Update a user
#     if john_doe:
#         db_manager.update_document(john_doe, age=31)

#    #Find a user you want to delete
#     user_to_delete = db_manager.find_document(User, query={"username": "john_doe"})

#     if user_to_delete:
#         # Delete the user
#         db_manager.delete_document(user_to_delete)
