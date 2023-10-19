import datetime
import json
from bson import ObjectId
from flask import Blueprint, request, Response, current_app
from models.common import DatabaseManager,User
from mongoengine.queryset.visitor import Q
from argon2 import PasswordHasher
from mongoengine.errors import NotUniqueError
import jwt

db_route = Blueprint('db', __name__)
dbManager = DatabaseManager()
dbManager.connect()

ph = PasswordHasher()

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

@db_route.route('/user/<user_id>', methods=['GET'])
def getUserById(user_id):
    if request.method == 'GET':
        try:
            print(user_id)
            query={"_id":ObjectId(user_id)}
            user = dbManager.findOne(User,query)
            r = Response(response=user.to_json(), status=200, mimetype="application/json")
        except:
            r = Response(response='{"message":"bad request"}', status=400, mimetype="application/json")
    return r

@db_route.route('/user-by-email/<email_id>', methods=['GET'])
def getUserByEmailId(email_id):
    try:
        if request.method == 'GET':
            print(email_id)
            query={"email":email_id}
            user = dbManager.findOne(User,query)
            r = Response(response=user.to_json(), status=200, mimetype="application/json")
    except:
        r = Response(response='{"message":"bad request"}', status=400, mimetype="application/json")
    return r

@db_route.route('/user', methods=['PUT'])
def UpdateUser():
    if request.method == 'PUT':
        try:      
            input = json.loads(request.data)  
            user_id=input["_id"] 
            print(type(user_id))
            query={"_id":ObjectId(user_id)}
            user = dbManager.findOne(User,query)
            input["updatedAt"]=datetime.datetime.utcnow
            dbManager.update(user, **input)
            print("User updated details:", user)
            r = Response(response=user.to_json(), status=200, mimetype="application/json")
        except:
            r = Response(response='{"message":"bad request"}', status=400, mimetype="application/json")
    return r

@db_route.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        try:
            user_data = request.get_json()
            new_user = User(**user_data)
            passwordHash = ph.hash(new_user.password)
            new_user.password = passwordHash
            new_user.save()
            del new_user.password
            return Response(response=new_user.to_json(), status=201, mimetype="application/json")
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
                    payload = {
                        'user_id': str(user.id),  
                        'email': user.email
                    }
                    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
                    user.token = token
                    user.updatedAt = datetime.datetime.utcnow
                    toUpdate = dict()
                    toUpdate['token'], toUpdate['updatedAt'] = user.token, user.updatedAt
                    print(toUpdate)
                    dbManager.update(user,**toUpdate)         
                    del user.id  
                    del user.password
                    return Response(response=user.to_json(), status=200, mimetype="application/json")
                else:
                    resp = {'message': 'Authentication Failed. Invalid Credentials'}
                    return Response(response=json.dumps(resp), status=401, mimetype="application/json")
            else:
                resp = {'message': 'Authentication Failed. Account does not exist'}
                return Response(response=json.dumps(resp), status=401, mimetype="application/json")
        except Exception as e:
            resp = {'message': 'Unexpected Error'}
            print("An unexpected error occurred:", str(e))
            return Response(response=json.dumps(resp), status=400, mimetype="application/json")


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