from flask import Response
from enum import Enum
import json
from collections import OrderedDict
import mongoengine

from models.common import toJson
 
class ResponseStatus(Enum):
    SUCCESS = 1
    BAD_REQUEST = 2
    UNAUTHORIZED = 3
    INVALID_TOKEN = 4
    INTERNAL_SERVER_ERROR = 5
    METHOD_NOT_ALLOWED=6

defaultResponse = {}

def flaskResponse(status, response = None):
    if status == ResponseStatus.SUCCESS:
        if response is None or response == True:
            defaultResponse['message'] = 'Success'
            response = defaultResponse
        elif response == False:
            defaultResponse['message'] = 'No record found for id'
            response = defaultResponse
        elif type(response) == str:
            defaultResponse['message'] = response
            response = defaultResponse
        
        elif type(response) == dict :
            response = json.dumps(toJson(response))
        elif type(response) == list :
            response = json.dumps(response)
        else: 
            response = json.dumps(toJson(response))

        return Response(response, status=200, mimetype="application/json")
    
    if status == ResponseStatus.BAD_REQUEST:
        defaultResponse['message'] = 'Bad Request'
        return Response(response=json.dumps(defaultResponse), status=400, mimetype="application/json")
    
    if status == ResponseStatus.UNAUTHORIZED:
        defaultResponse['message'] = 'Unauthorized Access'
        return Response(response=json.dumps(defaultResponse), status=400, mimetype="application/json")
    
    if status == ResponseStatus.INVALID_TOKEN:
        defaultResponse['message'] = 'Invalid Token'
        return Response(response=json.dumps(defaultResponse), status=401, mimetype="application/json")
    
    if status == ResponseStatus.INTERNAL_SERVER_ERROR:
        defaultResponse['message'] = 'Internal Server Error'
        if response != None:
            defaultResponse['message'] = 'Error'
            defaultResponse['error'] = response
        return Response(response=json.dumps(defaultResponse), status=500, mimetype="application/json")
    
    if status == ResponseStatus.METHOD_NOT_ALLOWED:
        return Response(response=json.dumps(defaultResponse), status=405, mimetype="application/json")
