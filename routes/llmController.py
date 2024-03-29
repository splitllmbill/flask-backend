from csv import reader
import uuid
import os
from flask import request, jsonify, Blueprint
import json
import google.generativeai as LLM
import PIL.Image
import traceback

llm_route = Blueprint('llm', __name__)

folder_path='uploads'
LLM.configure(api_key=os.getenv('LLM_API_KEY'))
models = [m.name for m in LLM.list_models()]
text_model_name = os.getenv("TEXT_MODEL")
ocr_model_name = os.getenv("OCR_MODEL")

text_model = [name for name in models if name.endswith(text_model_name)]
ocr_model = [name for name in models if name.endswith(ocr_model_name)]


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
    if len(ocr_model) == 0:
        return jsonify({'message': 'Exception while calling Gemini API. Vision model not found', 'llmoutput': {}})
    try:
        model = LLM.GenerativeModel(ocr_model[0])
        safety_settings = [
        {
            "category": "HARM_CATEGORY_DANGEROUS",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
        ]
        response = model.generate_content(["Extract necessary information from this bill image of the items excluding tax and service charges into a JSON array with objects having properties - slno, item name, quantity, amount and total amount. Map that JSON array to a field called items in the final result. Also another field tax should be mapped to a json array having fields like type, percent and amount. Bill image: ", img],safety_settings=safety_settings)
        response.resolve()
        result = response.text.replace('`','').replace('json','').strip()
        result = response.text
        res = json.loads(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': 'Exception while calling Gemini API', 'llmoutput': {}})
    return jsonify({'message': 'File uploaded successfully', 'filename': unique_filename, 'ocroutput': res})
    
@llm_route.route('/expense', methods=['POST'])
def convert_expense():
    prompt = "Create a JSON array containing the fields 'name', 'category' and 'amount' only to represent the expense details of Input. Make sure to use title case for the name and category. If words like relative time are used then represent yesterday as -1, tomorrow as +1 etc. Input: "
    data = request.get_json() 
    sentence = data.get('requestData', 0)['sentence']
    prompt+=sentence
    if len(text_model) == 0:
        return jsonify({'message': 'Exception while calling Gemini API. Text model not found', 'llmoutput': {}})
    model = LLM.GenerativeModel(text_model[0])
    response = model.generate_content(prompt)
    response.resolve()
    jsonResponse = response.text[8:-4]
    try:
        jsonResponse = json.loads(jsonResponse)
    except json.JSONDecodeError as E:
        print(E)
        print(response.text)
        jsonResponse = None
    if jsonResponse is None:
        return jsonify({'message': 'Exception while calling Gemini API', 'llmoutput': {}})
    return jsonify({'message': 'Expense Processed Successfully', 'llmoutput': jsonResponse})
        

@llm_route.route('/home', methods=['GET'])
def home():
    return 'Welcome to home'