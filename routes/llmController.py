from csv import reader
import uuid
import os
from flask import request, jsonify, Blueprint
import json
import google.generativeai as LLM
import PIL.Image
import traceback
from services import promptService
from util.requestHandler import requestHandler
from util.response import flaskResponse, ResponseStatus

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
@requestHandler
def upload_file(userId, request):
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
        promptDocument = promptService.getPrompt('bill')
        prompt = promptDocument['prompt']
        response = model.generate_content([prompt, img],safety_settings=safety_settings)
        response.resolve()
        promptDocument['hits']+=1
        result = response.text.replace('`','').replace('json','').replace('JSON','').strip()
        res = json.loads(result)
    except Exception:
        traceback.print_exc()
        promptDocument['failureHits']+=1
        promptDocument.save()
        return jsonify({'message': 'Exception while calling Gemini API', 'llmoutput': {}})
    promptDocument['successHits']+=1
    promptDocument.save()
    return flaskResponse(ResponseStatus.SUCCESS,{'message': 'File uploaded successfully', 'filename': unique_filename, 'ocroutput': res})
    
@llm_route.route('/expense', methods=['POST'])
@requestHandler
def convert_expense(userId, request):
    if len(text_model) == 0:
        return flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR,{'message': 'Exception while calling Gemini API. Text model not found', 'llmoutput': {}})
    promptDocument = promptService.getPrompt('chat')
    prompt = promptDocument['prompt']
    data = request.get_json()
    sentence = data.get('requestData', 0)['sentence']
    prompt+=sentence
    try:
        model = LLM.GenerativeModel(text_model[0])
        response = model.generate_content(prompt)
        response.resolve()
        promptDocument['hits']+=1
        result = response.text
        formatted = result.replace('`','').replace('json','').replace('JSON','').strip()
        jsonResponse = json.loads(formatted)
        jsonArray = [dict((k.lower(), v) for k, v in i.items()) for i in jsonResponse]
    except Exception as e:
        traceback.print_exc()
        print('API Response: ',result)
        promptDocument['failureHits']+=1
        promptDocument.save()
        return flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR,{'message': 'Exception while calling Gemini API', 'llmoutput': {}, 'error': str(e)})
    promptDocument['successHits']+=1
    promptDocument.save()
    return flaskResponse(ResponseStatus.SUCCESS,{'message': 'Expense Processed Successfully', 'llmoutput': jsonArray})
        
@llm_route.route('/home', methods=['GET'])
def home():
    return 'Welcome to home'