import os
import traceback
from google import genai
from google.genai import types
import PIL.Image
import json

# Function to generate OCR content from an image
def generate_ocr_content(image, prompt):
    try:
        client = genai.Client(api_key=os.getenv('LLM_API_KEY'))
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(
                        category='HARM_CATEGORY_DANGEROUS_CONTENT',
                        threshold='BLOCK_NONE'
                    ),
                    types.SafetySetting(
                        category='HARM_CATEGORY_HARASSMENT',
                        threshold='BLOCK_NONE'
                    ),
                    types.SafetySetting(
                        category='HARM_CATEGORY_HATE_SPEECH',
                        threshold='BLOCK_NONE'
                    ),
                    types.SafetySetting(
                        category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                        threshold='BLOCK_NONE'
                    )
                ]
            )
        )
        
        result = response.text.replace('`', '').replace('json', '').replace('JSON', '').strip()
        return result, None
    except Exception as e:
        traceback.print_exc()
        return None, str(e)

# Function to generate text content for expense processing
def generate_text_content(prompt):
    try:
        client = genai.Client(api_key=os.getenv('LLM_API_KEY'))
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        
        result = response.text.replace('`', '').replace('json', '').replace('JSON', '').strip()
        return result, None
    except Exception as e:
        traceback.print_exc()
        return None, str(e)
