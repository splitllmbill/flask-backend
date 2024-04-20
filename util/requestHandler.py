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
            error_message = f"{type(e).__name__}: {e}"
            print(f"Error at {request.path}: {error_message}")
            return flaskResponse(ResponseStatus.INVALID_TOKEN,str(e))
        except (BadRequest, ValueError) as e:
            error_message = f"{type(e).__name__}: {e}"
            print(f"Error at {request.path}: {error_message}")
            return flaskResponse(ResponseStatus.BAD_REQUEST,str(e))
        except Exception as e:
            error_message = f"{type(e).__name__}: {e}"
            print(f"Error at {request.path}: {error_message}")
            return flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR,str(e))
    return decorated_function