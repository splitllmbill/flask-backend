from flask import Blueprint, request, Response
from models.common import DatabaseManager,User

db_route = Blueprint('db', __name__)

# db_manager.connect()

@db_route.route('/userList', methods=['GET'])
def userList():
    if request.method == 'GET':
        users =User.objects
        r = Response(response=users.to_json(), status=200, mimetype="application/json")
    return r

@db_route.route('/createUser', methods=['POST'])
def createUser():
    if request.method == 'POST':
        user = User(name='sivaganesh',email='s@g.com',password='hello')
        user.save()
        r = Response(response=user.to_json(), status=200, mimetype="application/json")
    return r

@db_route.route('/users', methods=['GET'])
def users():
    query = {}
    result = DatabaseManager.find('user', query)
    print(result)
    l = []
    for document in result:
        l.append(document)
    return l

# save object to collection
# db_manager.insert_document(User, username="jane_doe", email="jane@example.com", age=25)

# Find all users
# all_users = db_manager.find_documents(User)

# Find a user with a specific username
# john_doe = db_manager.find_document(User, query={"username": "john_doe"})

# Update a user
# if john_doe:
#     db_manager.update_document(john_doe, age=31)

#Find a user you want to delete
# user_to_delete = db_manager.find_document(User, query={"username": "john_doe"})

# Delete the user
# if user_to_delete:
#     db_manager.delete_document(user_to_delete)