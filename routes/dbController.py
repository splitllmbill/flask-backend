import datetime
import json
from bson import ObjectId
from flask import Blueprint, request, Response, current_app
from werkzeug.exceptions import BadRequest
from util.response import ResponseStatus, flaskResponse
from mongoengine.queryset.visitor import Q
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from mongoengine.errors import NotUniqueError
import jwt

from services import expenseService,eventService,shareService, friendService
from models.common import Account, DatabaseManager,User, toJson
from util.auth import validate_jwt_token
from util.response import ResponseStatus, flaskResponse
from util.requestHandler import requestHandler

db_route = Blueprint('db', __name__)
dbManager = DatabaseManager()
dbManager.connect()

ph = PasswordHasher()

@db_route.route('/user', methods=['GET'])
@requestHandler
def getUserById(userId, request):
    if request.method == 'GET':
        try:
            validate_jwt_token(request)
            query={"id":ObjectId(userId)}
            user = dbManager.findOne(User,query)
            r=flaskResponse(ResponseStatus.SUCCESS,user)

        except jwt.PyJWTError as e:
            print(e)
            r = flaskResponse(ResponseStatus.INVALID_TOKEN)
        
        except (BadRequest,ValueError) as e:
            print(e)
            r = flaskResponse(ResponseStatus.BAD_REQUEST)

        except Exception as e:
            print(e)
            r = flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR)
    else:
        r = flaskResponse(ResponseStatus.METHOD_NOT_ALLOWED)
    return r

@db_route.route('/users', methods=['GET'])
def getAllUsers():
    if request.method == 'GET':
        try:
            validate_jwt_token(request)
            query={}
            users = dbManager.findAll(User,query)
            r=flaskResponse(ResponseStatus.SUCCESS,[toJson({"id":user.id,"email":user.email,"name":user.name}) for user in users])

        except jwt.PyJWTError as e:
            print(e)
            r = flaskResponse(ResponseStatus.INVALID_TOKEN)
        
        except (BadRequest,ValueError) as e:
            print(e)
            r = flaskResponse(ResponseStatus.BAD_REQUEST)

        except Exception as e:
            print(e)
            r = flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR)
    else:
        r = flaskResponse(ResponseStatus.METHOD_NOT_ALLOWED)
    return r

@db_route.route('/user-by-email/<email_id>', methods=['GET'])
def getUserByEmailId(email_id):
    if request.method == 'GET':
        try:  
            # validate_jwt_token(request)
            print(email_id)
            query={"email":email_id}
            user = dbManager.findOne(User,query)
            r=flaskResponse(ResponseStatus.SUCCESS,user)

        except jwt.PyJWTError as e:
            print(e)
            r = flaskResponse(ResponseStatus.INVALID_TOKEN)
        
        except (BadRequest,ValueError) as e:
            print(e)
            r = flaskResponse(ResponseStatus.BAD_REQUEST)

        except Exception as e:
            print(e)
            r = flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR)
    else:
        r = flaskResponse(ResponseStatus.METHOD_NOT_ALLOWED)
    return r

@db_route.route('/user', methods=['PUT'])
def UpdateUser():
    if request.method == 'PUT':
        try:
            validate_jwt_token(request)      
            input = json.loads(request.data)  
            user_id=input["id"] 
            print(type(user_id))
            query={"id":ObjectId(user_id)}
            user = dbManager.findOne(User,query)
            input["updatedAt"]=datetime.datetime.utcnow
            dbManager.update(user, **input)
            print("User updated details:", user)
            r = Response(response=toJson(user), status=200, mimetype="application/json")
        except jwt.PyJWTError as e:
            print(e)
            r = flaskResponse(ResponseStatus.INVALID_TOKEN)
    
        except (BadRequest,ValueError) as e:
            print(e)
            r = flaskResponse(ResponseStatus.BAD_REQUEST)

        except Exception as e:
            print(e)
            r = flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR)

    else:
        r = flaskResponse(ResponseStatus.METHOD_NOT_ALLOWED)
    return r

@db_route.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        try:
            user_data = request.get_json()
            new_user = User(**user_data)
            passwordHash = ph.hash(new_user.password)
            new_user.password = passwordHash
            new_user.createdAt = datetime.datetime.utcnow
            new_user.updatedAt = datetime.datetime.utcnow
            new_user.save()
            new_account = Account()
            new_account.updatedAt = datetime.datetime.utcnow
            new_account.userId = new_user.id
            new_account.save()
            toUpdate = dict()
            toUpdate['updatedAt'] = datetime.datetime.utcnow
            toUpdate['account'] = new_account.id
            dbManager.update(new_user,**toUpdate)
            del new_user.createdAt, new_user.updatedAt, new_user.password, new_user.account
            return Response(response=json.dumps(toJson(new_user)), status=201, mimetype="application/json")
        except NotUniqueError as e:
            resp = {'message': 'Email address is already in use. Please choose another.'}
            print(e,resp)
            return Response(response=json.dumps(resp), status=400, mimetype="application/json")
        except Exception as e:
            resp = {'message': 'Bad Request'}
            print(e,resp)
            return Response(response=json.dumps(resp), status=400, mimetype="application/json")
    
@db_route.route('/login',methods=['POST'])
def loginUser():
    if request.method == 'POST':
        try:
            login_data = request.get_json()
            email = login_data.get('email')
            password = login_data.get('password')
            query={"email":email}
            user = dbManager.findOne(User,query)
            if user:
                if ph.verify(user.password, password):
                    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=24*60)
                    payload = {
                        'user_id': str(user.id),              
                        'email': user.email,
                        'exp': expiration_time
                    }
                    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
                    toUpdate = dict()
                    toUpdate['token'], toUpdate['updatedAt'] = token, datetime.datetime.utcnow
                    dbManager.update(user,**toUpdate)         
                    del user.id, user.password, user.createdAt, user.updatedAt, user.account
                    return flaskResponse(ResponseStatus.SUCCESS, user)
            else:
                resp = {'message': 'Authentication Failed. Account does not exist'}
                return Response(response=json.dumps(resp), status=401, mimetype="application/json")
        except VerifyMismatchError as e:
            resp = {'message': 'Authentication Failed. Invalid Credentials'}
            return Response(response=json.dumps(resp), status=401, mimetype="application/json")
        except Exception as e:
            resp = {'message': 'Internal Server Error'}
            print('Exception during login',e,type(e))
            return Response(response=json.dumps(resp), status=500, mimetype="application/json")
        
@db_route.route('/logout',methods=['POST'])
def logoutUser():
    if request.method == 'POST':
        try:
            # TODO - Token validation instead of email from request body
            login_data = request.get_json()
            email = login_data.get('email')
            query={"email":email}
            user = dbManager.findOne(User,query)
            toUpdate = dict()
            toUpdate['token'] = None
            dbManager.update(user,**toUpdate)
            resp = {'message': 'Logout Successful'}
            return Response(response=json.dumps(resp), status=200, mimetype="application/json")
        except Exception as e:
            resp = {'message': 'Internal Server Error'}
            print('Exception during login',e,type(e))
            return Response(response=json.dumps(resp), status=500, mimetype="application/json")

@db_route.route('/account', methods=['PUT'])
@requestHandler
def updateAccount(userId):
    requestData = request.get_json()
    query = {
        "id": ObjectId(userId)
    }
    user = dbManager.findOne(User, query)
    dbManager.update(user.account, **requestData)
    return flaskResponse(ResponseStatus.SUCCESS)

@db_route.route('/expense/<expenseId>', methods = ['GET'])
@requestHandler
def getExpenseById(userId, request, expenseId):
    expense = expenseService.getExpenseById(expenseId, userId)
    return flaskResponse(ResponseStatus.SUCCESS, expense)

@db_route.route('/expense/nongroup', methods = ['GET'])
@requestHandler
def getNonGroupExpenses(userId, request):
    expense = friendService.getNonGroupExpenses(userId)
    return flaskResponse(ResponseStatus.SUCCESS, expense)

@db_route.route('/expenses/personal', methods=['GET'])
@requestHandler
def getAllExpensesForUser(userId, request):
    try:
        expenses = expenseService.getAllExpensesForUser(userId)
        return flaskResponse(ResponseStatus.SUCCESS, [toJson(expense) for expense in expenses])
    except Exception as e:
        print(f"Error in getAllExpensesForUser route: {e}")
        return flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR, str(e))

@db_route.route('/expense', methods = ['POST'])
@requestHandler
def createExpense(userId, request):
    print(request)
    requestData = request.get_json()
    expense = expenseService.createExpense(userId,requestData)
    return flaskResponse(ResponseStatus.SUCCESS, expense)

@db_route.route('/expense/<expenseId>', methods = ['PUT'])
@requestHandler
def updateExpense(userId, request, expenseId):
    requestData = request.get_json()
    expense = expenseService.updateExpense(userId,expenseId,requestData)
    return flaskResponse(ResponseStatus.SUCCESS, expense)

@db_route.route('/expense/<expenseId>', methods = ['DELETE'])
@requestHandler
def deleteExpense(userId, request, expenseId):
    status = expenseService.deleteExpense(expenseId)
    return flaskResponse(ResponseStatus.SUCCESS,status)

@db_route.route('user/events', methods=['GET'])
@requestHandler
def getUserEvents(userId, request):
        session_user_id = validate_jwt_token(request)
        events=eventService.getUserEvents(userId)
        return flaskResponse(ResponseStatus.SUCCESS, events)
    

@db_route.route('event/<event_id>/expenses', methods=['GET'])
@requestHandler
def getEventExpenses(userId, request, event_id):
    expenses=expenseService.getEventExpensesAlongWithUserSummary(userId, event_id)
    return flaskResponse(ResponseStatus.SUCCESS,expenses)

@db_route.route('expense/<expense_id>/shares', methods=['GET'])
@requestHandler
def getExpenseShares(userId, request, expense_id):
    shares=shareService.getExpenseShares(userId, expense_id)
    return flaskResponse(ResponseStatus.SUCCESS,shares)
    

@db_route.route('event/<event_id>/dues', methods=['GET'])
def getEventDues(event_id):
    if request.method == 'GET':
        try:   
            session_user_id = validate_jwt_token(request)
            result=eventService.getEventDues(event_id)
            print(result)
            r= flaskResponse(ResponseStatus.SUCCESS,result.__dict__)
        except jwt.PyJWTError as e:
            print(e)
            r = flaskResponse(ResponseStatus.INVALID_TOKEN)
        
        except (BadRequest,ValueError) as e:
            print(e)
            r = flaskResponse(ResponseStatus.BAD_REQUEST)

        except Exception as e:
            print(e)
            r = flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR)
    else:
        r = flaskResponse(ResponseStatus.METHOD_NOT_ALLOWED)
    return r

@db_route.route('user/event/<event_id>/dues', methods=['GET'])
@requestHandler
def getEventDuesForUser(user_id,request,event_id):
    session_user_id = validate_jwt_token(request)
    result=eventService.getEventDuesForUser(event_id,user_id)
    return flaskResponse(ResponseStatus.SUCCESS,result)

@db_route.route('/event', methods=['POST'])
def createEvent():
    if request.method == 'POST':
        try:   
            session_user_id = validate_jwt_token(request)
            requestData = request.get_json()
            if "id" in requestData.keys():
                del(requestData["id"])
            result=eventService.saveEvent(session_user_id,requestData)
            r=flaskResponse(ResponseStatus.SUCCESS,result)
        except jwt.PyJWTError as e:
            print(e)
            r = flaskResponse(ResponseStatus.INVALID_TOKEN)
        
        except (BadRequest,ValueError) as e:
            print(e)
            r = flaskResponse(ResponseStatus.BAD_REQUEST)

        except Exception as e:
            print(e)
            r = flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR)
    else:
        r = flaskResponse(ResponseStatus.METHOD_NOT_ALLOWED)
    return r

@db_route.route('/event', methods=['PUT'])
def updateEvent():
    if request.method == 'PUT':
        try:   
            session_user_id = validate_jwt_token(request)
            requestData = request.get_json()
            if "id" not in requestData.keys():
                r = flaskResponse(ResponseStatus.BAD_REQUEST)
                return
            result=eventService.saveEvent(session_user_id,requestData)
            r=flaskResponse(ResponseStatus.SUCCESS,result)
        except jwt.PyJWTError as e:
            print(e)
            r = flaskResponse(ResponseStatus.INVALID_TOKEN)
        
        except (BadRequest,ValueError) as e:
            print(e)
            r = flaskResponse(ResponseStatus.BAD_REQUEST)

        except Exception as e:
            print(e)
            r = flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR)
    else:
        r = flaskResponse(ResponseStatus.METHOD_NOT_ALLOWED)
    return r

@db_route.route('/event/<event_id>', methods=['GET'])
def getEvent(event_id):
    session_user_id = validate_jwt_token(request)
    event=eventService.getEventByID(event_id)
    r=flaskResponse(ResponseStatus.SUCCESS,event)
    return r

@db_route.route('/event/<event_id>', methods=['DELETE'])
def deleteEvent(event_id):
    session_user_id = validate_jwt_token(request)
    result=eventService.deleteEvent(event_id)
    r=flaskResponse(ResponseStatus.SUCCESS,result)
    return r

@db_route.route('/user/friends', methods=['GET'])
@requestHandler
def get_user_friends(user_id, request):
    result = friendService.get_friend_list(user_id);
    return flaskResponse(ResponseStatus.SUCCESS,result);

@db_route.route('/user/expense/friend/<friend_id>', methods=['GET'])
@requestHandler
def getFriendExpenses(user_id, request, friend_id):
    result = friendService.getFriendDetails(user_id,friend_id);
    return flaskResponse(ResponseStatus.SUCCESS,result);


@db_route.route('/<type>/<id>/users', methods=['GET'])
@requestHandler
def getEventUsers(user_id, request, type, id):
    result = eventService.getEventOrFriendUsers(user_id,type,id);
    return flaskResponse(ResponseStatus.SUCCESS,result);
