import uuid
import os
# import easyocr
from flask import request, jsonify, Blueprint,current_app
from dotenv import load_dotenv
import google.generativeai as palm
import json

llm_route = Blueprint('llm', __name__)

# reader = easyocr.Reader(['en'])
load_dotenv()
folder_path='uploads'
palm.configure(api_key=os.getenv('LLM_API_KEY'))
models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
model = models[0].name

# Function to check if the folder for uploads exists, and create it if not
def create_upload_folder():
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def generate_unique_filename(filename):
    # Generate a unique filename using a combination of timestamp and a random string
    unique_filename = str(uuid.uuid4()) + '_' + filename
    return unique_filename

# @llm_route.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file part'})
#     file = request.files['file']

#     if file.filename == '':
#         return jsonify({'error': 'No selected file'})
    
#     create_upload_folder()
#     unique_filename = generate_unique_filename(file.filename)
#     file.save(os.path.join(folder_path, unique_filename))
#     result = reader.readtext(os.path.join(current_app.config['UPLOADS_PATH'], unique_filename),detail=0)
#     prompt = 'Extract necessary information from this bill OCR output data containing all the food items and tax information into a JSON array with objects having properties - slno, item name, quantity, amount and total amount. Bill data: '
#     completion = palm.generate_text(
#         model=model,
#         prompt=prompt+(' '.join(result)),
#         temperature=0,
#         max_output_tokens=800,
#     )
#     print(json.loads(completion.result)[0])
#     return jsonify({'message': 'File uploaded successfully', 'filename': unique_filename, 'ocroutput': json.loads(completion.result)[0]})
    
@llm_route.route('/expense', methods=['POST'])
def convert_expense():
    prompt = "Create a JSON array containing the fields 'name', 'category', 'amount'  and 'date' to represent the expense details of Input. Make sure to use title case for the name and category. If words like relative time are used then represent yesterday as -1, tomorrow as +1 etc. Input: "
    data = request.get_json() 
    sentence = data.get('requestData', 0)['sentence']
    prompt+=sentence
    completion = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=0,
        max_output_tokens=800,
    )
    return jsonify({'message': 'Expense Processed Successfully', 'llmoutput': json.loads(completion.result)})

@llm_route.route('/home', methods=['GET'])
def home():
    return 'Welcome to home'