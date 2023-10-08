import os
from flask import Flask, request, jsonify
import easyocr
import uuid
reader = easyocr.Reader(['en'])

app = Flask(__name__)

# Set the upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'

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

        result = reader.readtext(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename),detail=0)

        return jsonify({'message': 'File uploaded successfully', 'filename': unique_filename, 'ocr': result})
    
@app.route('/expense', methods=['POST'])
def calculate_expense():
    if request.method == 'POST':
        data = request.get_json() 
        sentence = data.get('requestData', 0)['sentence']

        response = {
            'responseData': sentence
        }

        return jsonify(response)

if __name__ == '__main__':
    app.run(port=8081,debug=True)

