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

def flaskResponse(status, response = None):
    if status == ResponseStatus.SUCCESS:
        if response is None:
            defaultResponse['message'] = 'Success'
            response = defaultResponse
        if response == False:
            defaultResponse['message'] = 'No record found for id'
            response = defaultResponse

        if type(response) == dict:
            response = json.dumps(response)
        else: 
            response = response.to_json()      

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
            defaultResponse['message'] = 'Success'
            defaultResponse['error'] = response
        return Response(response=json.dumps(defaultResponse), status=401, mimetype="application/json")