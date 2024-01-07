import uuid
import os
from flask import request, jsonify, Blueprint
import json
import google.generativeai as LLM
import PIL.Image

llm_route = Blueprint('llm', __name__)

folder_path='uploads'
LLM.configure(api_key=os.getenv('LLM_API_KEY'))
models = [m.name for m in LLM.list_models()]
text_model = models[3]
ocr_model = models[4]

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
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    create_upload_folder()
    unique_filename = generate_unique_filename(file.filename)
    file.save(os.path.join(folder_path, unique_filename))
    with open(os.path.join(folder_path, unique_filename), 'rb') as f:
        file_content = f.read()

    img = PIL.Image.open(os.path.join(folder_path, unique_filename))
    model = LLM.GenerativeModel(ocr_model)
    response = model.generate_content(["Extract necessary information from this bill OCR output data containing all the food items and tax information into a JSON array with objects having properties - slno, item name, quantity, amount and total amount. Bill data:", img], stream=True)
    response.resolve();
    return jsonify({'message': 'File uploaded successfully', 'filename': unique_filename, 'ocroutput': json.loads(response.text[9:-4])})
    
@llm_route.route('/expense', methods=['POST'])
def convert_expense():
    prompt = "Create a JSON array containing the fields 'name', 'category', 'amount'  and 'date' to represent the expense details of Input. Make sure to use title case for the name and category. If words like relative time are used then represent yesterday as -1, tomorrow as +1 etc. Input: "
    data = request.get_json() 
    sentence = data.get('requestData', 0)['sentence']
    prompt+=sentence
    model = LLM.GenerativeModel(text_model)
    response = model.generate_content(prompt)
    return jsonify({'message': 'Expense Processed Successfully', 'llmoutput': json.loads(response.text[4:-4])})

@llm_route.route('/home', methods=['GET'])
def home():
    return 'Welcome to home'