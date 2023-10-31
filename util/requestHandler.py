from functools import wraps
from flask import request
from util.auth import validate_jwt_token
from util.response import flaskResponse, ResponseStatus
from werkzeug.exceptions import BadRequest
import jwt

def requestHandler(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        try:
            userId = validate_jwt_token(request)
            return function(userId, request, *args, **kwargs)
        except jwt.PyJWTError as e:
            print(e)
            return flaskResponse(ResponseStatus.INVALID_TOKEN)
        except (BadRequest, ValueError) as e:
            print(e)
            return flaskResponse(ResponseStatus.BAD_REQUEST)
        except Exception as e:
            print(e)
            return flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR)
    return decorated_function