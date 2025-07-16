from csv import reader
import uuid
import os
from flask import request, jsonify, Blueprint
import json
import PIL.Image
import traceback
from services import promptService, llmService
from util.requestHandler import requestHandler
from util.response import flaskResponse, ResponseStatus

llm_route = Blueprint('llm', __name__)

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
    promptDocument = promptService.getPrompt('bill')
    prompt = promptDocument['prompt']
    result, error = llmService.generate_ocr_content(img, prompt)
    if error:
        promptDocument['failureHits']+=1
        promptDocument.save()
        return jsonify({'message': f'Exception while calling Gemini API: {error}', 'llmoutput': {}})
    promptDocument['hits']+=1
    res = json.loads(result)
    promptDocument['successHits']+=1
    promptDocument.save()
    return flaskResponse(ResponseStatus.SUCCESS,{'message': 'File uploaded successfully', 'filename': unique_filename, 'ocroutput': res})
    
@llm_route.route('/expense', methods=['POST'])
@requestHandler
def convert_expense(userId, request):
    promptDocument = promptService.getPrompt('chat')
    prompt = promptDocument['prompt']
    data = request.get_json()
    sentence = data.get('requestData', 0)['sentence']
    prompt += sentence
    result, error = llmService.generate_text_content(prompt)
    if error:
        promptDocument['failureHits']+=1
        promptDocument.save()
        return flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR,{'message': f'Exception while calling Gemini API: {error}', 'llmoutput': {}})
    promptDocument['hits']+=1
    formatted = result
    jsonResponse = json.loads(formatted)
    jsonArray = [dict((k.lower(), v) for k, v in i.items()) for i in jsonResponse]
    promptDocument['successHits']+=1
    promptDocument.save()
    return flaskResponse(ResponseStatus.SUCCESS,{'message': 'Expense Processed Successfully', 'llmoutput': jsonArray})
        
@llm_route.route('/home', methods=['GET'])
def home():
    return 'Welcome to home'
