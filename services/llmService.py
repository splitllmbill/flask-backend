import os
import google.generativeai as LLM
import PIL.Image
import traceback

# Initialize LLM API with key from environment variables
def initialize_llm():
    LLM.configure(api_key=os.getenv('LLM_API_KEY'))
    models = [m.name for m in LLM.list_models()]
    text_model_name = os.getenv("TEXT_MODEL")
    ocr_model_name = os.getenv("OCR_MODEL")
    text_models = [name for name in models if name.endswith(text_model_name)]
    ocr_models = [name for name in models if name.endswith(ocr_model_name)]
    return text_models, ocr_models

# Function to generate OCR content from an image
def generate_ocr_content(image, prompt):
    text_models, ocr_models = initialize_llm()
    if not ocr_models:
        return None, "Vision model not found"
    
    try:
        model = LLM.GenerativeModel(ocr_models[0])
        safety_settings = [
            {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        response = model.generate_content([prompt, image], safety_settings=safety_settings)
        response.resolve()
        result = response.text.replace('`', '').replace('json', '').replace('JSON', '').strip()
        return result, None
    except Exception as e:
        traceback.print_exc()
        return None, str(e)

# Function to generate text content for expense processing
def generate_text_content(prompt):
    text_models, ocr_models = initialize_llm()
    if not text_models:
        return None, "Text model not found"
    
    try:
        model = LLM.GenerativeModel(text_models[0])
        response = model.generate_content(prompt)
        response.resolve()
        result = response.text.replace('`', '').replace('json', '').replace('JSON', '').strip()
        return result, None
    except Exception as e:
        traceback.print_exc()
        return None, str(e)
