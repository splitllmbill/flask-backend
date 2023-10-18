import easyocr
import uuid
import os
from flask import request, jsonify, Blueprint, current_app

llm_route = Blueprint('llm', __name__)

reader = easyocr.Reader(['en'])
folder_path='uploads'

# Function to check if the folder for uploads exists, and create it if not
def create_upload_folder():
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def generate_unique_filename(filename):
    # Generate a unique filename using a combination of timestamp and a random string
    unique_filename = str(uuid.uuid4()) + '_' + filename
    return unique_filename

@llm_route.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        
        create_upload_folder()
        unique_filename = generate_unique_filename(file.filename)
        file.save(os.path.join(folder_path, unique_filename))
        result = reader.readtext(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename),detail=0)
        return jsonify({'message': 'File uploaded successfully', 'filename': unique_filename, 'ocr': "success"})
    
@llm_route.route('/expense', methods=['POST'])
def calculate_expense():
    if request.method == 'POST':
        data = request.get_json() 
        sentence = data.get('requestData', 0)['sentence']

        response = {
            'responseData': sentence
        }

        return jsonify(response)