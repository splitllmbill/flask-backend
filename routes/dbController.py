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

from services import expenseService,eventService,shareService
from models.common import Account, DatabaseManager,User
from util.auth import validate_jwt_token
from util.response import ResponseStatus, flaskResponse
from util.requestHandler import requestHandler

db_route = Blueprint('db', __name__)
dbManager = DatabaseManager()
dbManager.connect()

ph = PasswordHasher()

@db_route.route('/user/<user_id>', methods=['GET'])
def getUserById(user_id):
    if request.method == 'GET':
        try:
            validate_jwt_token(request)
            query={"id":ObjectId(user_id)}
            user = dbManager.findOne(User,query)
            r = Response(response=user.to_json(), status=200, mimetype="application/json")

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
            r = Response(response=user.to_json(), status=200, mimetype="application/json")

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
            r = Response(response=user.to_json(), status=200, mimetype="application/json")
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
            return Response(response=json.dumps(new_user.to_json()), status=201, mimetype="application/json")
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
    expense = expenseService.getExpenseById(expenseId)
    return flaskResponse(ResponseStatus.SUCCESS, expense)

@db_route.route('/expense', methods = ['POST'])
@requestHandler
def createExpense(userId, request):
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
    

@db_route.route('user/<user_id>/events', methods=['GET'])
def getUserEvents(user_id):
    if request.method == 'GET':
        try:   
            session_user_id = validate_jwt_token(request)
            events=eventService.getUserEvents(user_id)
            return Response(response=events.to_json(), status=200, mimetype="application/json")
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

@db_route.route('event/<event_id>/expenses', methods=['GET'])
def getEventExpenses(event_id):
    if request.method == 'GET':
        try:   
            session_user_id = validate_jwt_token(request)
            expenses=expenseService.getEventExpenses(event_id)
            return Response(response=expenses.to_json(), status=200, mimetype="application/json")
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

@db_route.route('expense/<expense_id>/shares', methods=['GET'])
def getExpenseShares(expense_id):
    if request.method == 'GET':
        try:   
            session_user_id = validate_jwt_token(request)
            shares=shareService.getExpenseShares(expense_id)
            return Response(response=shares.to_json(), status=200, mimetype="application/json")
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


@db_route.route('event/<event_id>/dues', methods=['GET'])
def getExpenseDues(event_id):
    if request.method == 'GET':
        try:   
            session_user_id = validate_jwt_token(request)
            result=eventService.getEventDues(event_id)
            return Response(response=json.dumps(result), status=200, mimetype="application/json")
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

# using model findall or find with query (use for custom queries)
# @db_route.route('/userList', methods=['GET'])
# def userList():
#     if request.method == 'GET':
#         query = Q(name='sivaganesh')
#         users =User.objects(query)
#         r = Response(response=users.to_json(), status=200, mimetype="application/json")
#     return r

# # using model to save
# @db_route.route('/createUser', methods=['POST'])
# def createUser():
#     if request.method == 'POST':
#         user = User(name='sivaganesh',email='s@g.com',password='hello')
#         user.save()
#         r = Response(response=user.to_json(), status=200, mimetype="application/json")
#     return r
# # usin db manager to findall
# @db_route.route('/user', methods=['GET'])
# def user():
#     if request.method == 'GET':
#         users = dbManager.findAll(User)
#         r = Response(response=users.to_json(), status=200, mimetype="application/json")
#     return r

# more examples using db manager

# user_data = {
#     'name': 'John Doe',
#     'email': 'john@example.com',
#     'phoneNumber': 1234567890,
#     'password': 'password123',
#     'token': 'random_token',
#     'createdAt': datetime.utcnow(),
#     'updatedAt': datetime.utcnow(),
# }

# # Save a user
# user = User(**user_data)
# db_manager.save(User, **user_data)

# # Find all users
# all_users = db_manager.findAll(User)
# print("All Users:", all_users)

# # Find one user by name
# query = {'name': 'John Doe'}
# user = db_manager.findOne(User, query)
# print("User found by name:", user)

# # Update user details
# updated_user_data = {'phoneNumber': 9876543210}
# db_manager.update(user, **updated_user_data)
# print("User updated details:", user)

# # Delete a user
# db_manager.delete(user)