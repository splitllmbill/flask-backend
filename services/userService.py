import secrets
import string
import uuid
from argon2 import PasswordHasher
from bson import ObjectId
from models.common import Account, DatabaseManager, User

dbManager = DatabaseManager()
dbManager.connect()

ph = PasswordHasher()

def getUserNameById(user_id):
    query = {
        "id": user_id
    }
    user = dbManager.findOne(User,query)
    if user is None:
        return False
    return user.name

def getUserAccount(userId):
    query1 = {
        "id": userId
    }
    user = dbManager.findOne(User, query1)
    if user is None or not hasattr(user, 'account'):
        return False
    
    query2 = {
        "id": ObjectId(user.account.id)
    }
    account = dbManager.findOne(Account, query2)
    if account is None:
        return False
    
    return {
        "uuid": user.uuid,
        "name": user.name,
        "email": user.email,
        "upiNumber": account.upiNumber if hasattr(account, 'upiNumber') else "",
        "upiId": account.upiId if hasattr(account, 'upiId') else ""
    }

def putUserAccount(userId, newData):
    # Assuming User and Account are classes representing user and account models, respectively
    user = User.objects.get(id=userId)
    if user is None or not hasattr(user, 'account'):
        return False
    
    account = Account.objects.get(id=user.account.id)
    if account is None:
        return False
    
    # Update account fields with new data
    if 'name' in newData:
        user.name = newData['name']
    if 'upiNumber' in newData:
        account.upiNumber = newData['upiNumber']
    if 'upiId' in newData:
        account.upiId = newData['upiId']
    
    # Save updated user and account objects
    user.save()
    account.save()
    
    return True

def generate_user_code():
    # Generate a UUID (Version 4) as a unique user code
    return str(uuid.uuid4())

def changePassword(userId, requestData):
    user = User.objects.get(id=userId)
    if user is None:
        return {"message":"User does not exist"}
    passwordHash = ph.hash(requestData['password'])
    user.password = passwordHash
    user.save()
    return {"message":"Password updated successfully"}

def forgotPassword(requestData):
    user = User.objects.get(email=requestData['email'])
    if user is None:
        return {"message":"User does not exist"}
    new_password = generate_random_password()  
    password_hash = ph.hash(new_password)  
    user.password = password_hash
    user.save()
    # Implement this function to send an email with the new password    
    return {
        "message": "Password reset successfully. Please check the console for the new password.",
        "new_password": new_password
    }


def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password
    