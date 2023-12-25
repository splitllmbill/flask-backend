import jwt
import datetime
from flask import current_app

def validate_jwt_token(request):
    token = None

    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    if not token:
        raise jwt.PyJWTError
    
    payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    current_time = datetime.datetime.utcnow()

    if 'exp' in payload and current_time > datetime.datetime.fromtimestamp(payload['exp']):
        raise jwt.ExpiredSignatureError
    
    return payload['user_id'] 