from flask import Response
from enum import Enum
import json
 
class ResponseStatus(Enum):
    SUCCESS = 1
    BAD_REQUEST = 2
    UNAUTHORIZED = 3
    INVALID_TOKEN = 4
    INTERNAL_SERVER_ERROR = 5

defaultResponse = {}

def flaskResponse(type, response = None):
    if type == ResponseStatus.SUCCESS:
        if response is None:
            defaultResponse['message'] = 'Success'
            response = defaultResponse
        if response == '':
            defaultResponse['message'] = 'No record found for id'
            response = defaultResponse
        return Response(response=json.dumps(response), status=200, mimetype="application/json")
    
    if type == ResponseStatus.BAD_REQUEST:
        defaultResponse['message'] = 'Bad Request'
        return Response(response=json.dumps(defaultResponse), status=400, mimetype="application/json")
    
    if type == ResponseStatus.UNAUTHORIZED:
        defaultResponse['message'] = 'Unauthorized Access'
        return Response(response=json.dumps(defaultResponse), status=400, mimetype="application/json")
    
    if type == ResponseStatus.INVALID_TOKEN:
        defaultResponse['message'] = 'Invalid Token'
        return Response(response=json.dumps(defaultResponse), status=401, mimetype="application/json")
    
    if type == ResponseStatus.INTERNAL_SERVER_ERROR:
        defaultResponse['message'] = 'Internal Server Error'
        if response != None:
            defaultResponse['message'] = 'Success'
            defaultResponse['error'] = response
        return Response(response=json.dumps(defaultResponse), status=401, mimetype="application/json")