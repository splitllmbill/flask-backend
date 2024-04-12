import datetime
import json
from bson import ObjectId
from flask import Blueprint, jsonify, request, Response, current_app, send_file
from werkzeug.exceptions import BadRequest
from util.response import ResponseStatus, flaskResponse
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from mongoengine.errors import NotUniqueError
import jwt

from services import expenseService,eventService,shareService, friendService, referralService, userService, verificationService, upiService, dashboardService, commonService
from models.common import Account, DatabaseManager,User, Referral, Verification, toJson

from util import generator, aes
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
            query={"id":ObjectId(user_id)}
            user = dbManager.findOne(User,query)
            input["updatedAt"]=datetime.datetime.now(datetime.timezone.utc)
            dbManager.update(user, **input)
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
            inviteCode = user_data['inviteCode']
            if inviteCode != current_app.config['ADMIN_CODE']: 
                referred_user = referralService.getUserByInviteCode(inviteCode)
                if not referred_user:
                    resp = {'message': 'Invalid Invite Code. Please try again'}
                    return Response(response=json.dumps(resp), status=400, mimetype="application/json")
            del user_data['inviteCode']
            
            # save user info
            new_user = User(**user_data)
            passwordHash = ph.hash(new_user.password)
            new_user.password = passwordHash
            new_user.createdAt = datetime.datetime.now(datetime.timezone.utc)
            new_user.updatedAt = datetime.datetime.now(datetime.timezone.utc)
            new_user.uuid = generator.codeGenerate(6)
            new_user.save()

            if inviteCode != current_app.config['ADMIN_CODE']: 
                referralService.addReferredUser(inviteCode,new_user.id)
            # save account info
            new_account = Account()
            new_account.createdAt = datetime.datetime.now(datetime.timezone.utc)
            new_account.updatedAt = datetime.datetime.now(datetime.timezone.utc)
            new_account.userId = new_user.id
            new_account.save()
            toUpdate = dict()
            toUpdate['updatedAt'] = datetime.datetime.now(datetime.timezone.utc)
            toUpdate['account'] = new_account.id
            dbManager.update(new_user,**toUpdate)


            # save referral info
            user_referral = Referral()
            user_referral.userId = new_user.id
            user_referral.count = 0
            user_referral.createdAt = datetime.datetime.now(datetime.timezone.utc)
            user_referral.updatedAt = datetime.datetime.now(datetime.timezone.utc)
            user_referral.inviteCode = generator.codeGenerate(6)
            user_referral.save()


            # save verification info
            user_verification = Verification()
            user_verification.userId = new_user.id
            user_verification.createdAt = datetime.datetime.now(datetime.timezone.utc)
            user_verification.updatedAt = datetime.datetime.now(datetime.timezone.utc)
            user_verification.save()

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
                if ph.verify(user.password, aes.decrypt(password)):
                    expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10000)
                    payload = {
                        'user_id': str(user.id),              
                        'email': user.email,
                        'exp': expiration_time
                    }
                    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
                    toUpdate = dict()
                    toUpdate['token'], toUpdate['updatedAt'] = token, datetime.datetime.now(datetime.timezone.utc)
                    dbManager.update(user,**toUpdate)
                    verified = verificationService.checkEmailVerified(user.id)
                    return flaskResponse(ResponseStatus.SUCCESS, {
                        "token": user.token,
                        "verified": verified,
                        "id": str(user.id)
                    })
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
@requestHandler
def logoutUser(userId, request):
    if request.method == 'POST':
        try:
            query={"id":userId}
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

@db_route.route('/user/account', methods=['PUT'])
@requestHandler
def updateUserAccount(userId, request):
    requestData = request.get_json()
    result = userService.updateUserAccount(userId,requestData)
    if not result:
        return flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR,'Failed to update account details')
    return flaskResponse(ResponseStatus.SUCCESS, result)

@db_route.route('/user/account', methods=['GET'])
@requestHandler
def getAccount(userId, request):
    account = userService.getUserAccount(userId)
    return flaskResponse(ResponseStatus.SUCCESS, account)

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

@db_route.route('/expenses/personal', methods=['POST'])
@requestHandler
def getAllExpensesForUser(userId, request):
    try:
        requestData = request.get_json()
        expenses = expenseService.getAllExpensesForUser(userId,requestData)
        return flaskResponse(ResponseStatus.SUCCESS, [toJson(expense) for expense in expenses])
    except Exception as e:
        print(f"Error in getAllExpensesForUser route: {e}")
        return flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR, str(e))

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
    result = expenseService.deleteExpense(expenseId)
    return flaskResponse(ResponseStatus.SUCCESS,result)

@db_route.route('user/events', methods=['GET'])
@requestHandler
def getUserEvents(userId, request):
        session_user_id = validate_jwt_token(request)
        try:
            events=eventService.getUserEvents(userId)
            return flaskResponse(ResponseStatus.SUCCESS, events)
        except Exception as e:
            print(f"Error in getUserEvents route: {e}")
            return flaskResponse(ResponseStatus.INTERNAL_SERVER_ERROR, str(e))
    

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
    result = friendService.get_friend_list(user_id)
    return flaskResponse(ResponseStatus.SUCCESS,result)

@db_route.route('/user/expense/friend/<friend_id>', methods=['GET'])
@requestHandler
def getFriendExpenses(user_id, request, friend_id):
    result = friendService.getFriendDetails(user_id,friend_id)
    if result:
        return flaskResponse(ResponseStatus.SUCCESS,result)
    return flaskResponse(ResponseStatus.BAD_REQUEST)

@db_route.route('/user/expense/friend/<friend_id>/settleup', methods=['POST'])
@requestHandler
def settleUpFriendDues(user_id, request, friend_id):
    result = friendService.settleUpFriendDues(user_id,friend_id)
    return flaskResponse(ResponseStatus.SUCCESS,result)

@db_route.route('/<type>/<id>/users', methods=['GET'])
@requestHandler
def getEventUsers(user_id, request, type, id):
    result = eventService.getEventOrFriendUsers(user_id,type,id)
    return flaskResponse(ResponseStatus.SUCCESS,result)

@db_route.route('/invite/generate', methods=['PUT'])
@requestHandler
def generateInvite(user_id, request):
    result = referralService.generateInviteCode(user_id)
    r=flaskResponse(ResponseStatus.SUCCESS,result)
    return r

@db_route.route('/addFriend', methods = ['POST'])
@requestHandler
def addFriend(userId, request):
    requestData = request.get_json()
    result = friendService.add_friend(userId,requestData)
    return result

@db_route.route('/deleteFriend', methods = ['DELETE'])
@requestHandler
def deleteFriend(userId, request):
    requestData = request.get_json()
    result = friendService.delete_friend(userId,requestData)
    return flaskResponse(ResponseStatus.SUCCESS,result)

@db_route.route('/changePassword', methods = ['PUT'])
@requestHandler
def changePassword(userId, request):
    requestData = request.get_json()
    result = userService.changePassword(userId,aes.decrypt(requestData['password']))
    return flaskResponse(ResponseStatus.SUCCESS,result)

@db_route.route('/forgotPassword', methods=['POST'])
def forgotPassword():
    requestData = request.get_json()
    if requestData is None:
        return jsonify({"error": "Request body is empty"}), 400
    result = userService.forgotPassword(requestData)
    return jsonify(result)

@db_route.route('/verification/generate', methods = ['POST'])
@requestHandler
def generateVerification(userId, request):
    requestData = request.get_json()
    codeType = requestData['type']
    result = verificationService.generateVerificationCode(userId,codeType)
    return result

@db_route.route('/verification/validate', methods = ['POST'])
@requestHandler
def verificationValidate(userId, request):
    requestData = request.get_json()
    codeType = requestData['type']
    code = requestData['code']
    field = requestData['field']
    result = verificationService.validateCode(userId,code,codeType,field)
    if not result:
        return flaskResponse(ResponseStatus.SUCCESS,'Invalid Verification Code')
    return flaskResponse(ResponseStatus.SUCCESS,result)

@db_route.route('/upi/link', methods = ['POST'])
@requestHandler
def generateUPILink(userId, request):
    requestData = request.get_json()
    dest_userId = requestData['destination']
    amount = requestData['amount']
    note = requestData['note']
    result = upiService.generateUPILink(dest_userId, amount, note)
    if not result:
        return flaskResponse(ResponseStatus.SUCCESS,False)
    return flaskResponse(ResponseStatus.SUCCESS,result)

@db_route.route('/upi/image', methods = ['POST'])
@requestHandler
def generateUPIQR(userId, request):
    requestData = request.get_json()
    dest_userId = requestData['destination']
    amount = requestData['amount']
    note = requestData['note']
    result = upiService.generateUPIQR(dest_userId, amount, note)
    if not result:
        return flaskResponse(ResponseStatus.SUCCESS,False)
    return send_file(
        result,
        mimetype='image/png',
        as_attachment=True,
        download_name='qr_code.png'
    )

@db_route.route('/dashboard/summary', methods=['POST'])
@requestHandler
def getDashboardSummary(userId, request):
    result = dashboardService.getSummaryForHomepage(userId,request.get_json())
    if(result):
        return flaskResponse(ResponseStatus.SUCCESS,result)
    else: 
        return flaskResponse(ResponseStatus.SUCCESS,False)
    
@db_route.route('/dashboard/chart', methods=['POST'])
@requestHandler
def getDashboardChart(userId, request):
    result = dashboardService.getDashboardChart(userId,request.get_json())
    if(result):
        return flaskResponse(ResponseStatus.SUCCESS,result)
    else: 
        return flaskResponse(ResponseStatus.SUCCESS,False)
    
@db_route.route('/bulk', methods = ['POST'])
def bulkUpdate():
    userService.bulkUpdate()
    return "Success"

@db_route.route('/filter-options', methods = ['POST'])
@requestHandler
def filterOptions(userId, request):
    print(request)
    requestData = request.get_json()
    expense = commonService.getFilterOptions(requestData)
    return flaskResponse(ResponseStatus.SUCCESS, expense)
