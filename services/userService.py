import datetime
import secrets
import string
from argon2 import PasswordHasher
from bson import ObjectId
from models.common import Account, DatabaseManager, User, Verification, Referral
from services import emailService 

dbManager = DatabaseManager()

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
    query = {
        "id": userId
    }
    user = dbManager.findOne(User, query)
    if user is None:
        print('User does not exist')
        return False
    
    query['userId'] = query.pop('id')
    account = dbManager.findOne(Account, query)
    if account is None:
        print('Account does not exist')
        return False
    
    verification = dbManager.findOne(Verification, query)
    if verification is None:
        print('Verification does not exist')
        return False
    
    referall = dbManager.findOne(Referral, query)
    if referall is None:
        print('Referral does not exist')
        return False
    
    verification = dbManager.findOne(Verification, query)
    if verification is None:
        return False
    
    referall = dbManager.findOne(Referral, query)
    if referall is None:
        return False
    
    return {
        "uuid": user.uuid,
        "name": user.name,
        "email": user.email,
        "upiNumber": account.upiNumber if hasattr(account, 'upiNumber') else '',
        "mobile": account.mobile if hasattr(account, 'mobile') else '',
        "upiId": account.upiId if hasattr(account, 'upiId') else '',
        "emailVerified": verification.emailVerified,
        "upiNumberVerified": verification.upiNumberVerified,
        "mobileVerified": verification.mobileVerified,
        "inviteCode": referall.inviteCode,
        "referralCount": referall.count
    }

def updateUserAccount(userId, newData):
    query={
        "id":ObjectId(userId)
    }
    user = dbManager.findOne(User,query)
    if user is None:
        return False
    query['userId'] = query.pop('id')
    account = dbManager.findOne(Account,query)    
    if account is None:
        return False
    
    if 'name' in newData:
        user.name = newData['name']
        user.updatedAt = datetime.datetime.now(datetime.timezone.utc)
        user.save()

    if 'upiId' in newData:
        account.upiId = newData['upiId']
        account.updatedAt = datetime.datetime.now(datetime.timezone.utc)
        account.save()

    if 'upiNumber' in newData:
        account.upiNumber = newData['upiNumber']
        account.updatedAt = datetime.datetime.now(datetime.timezone.utc)
        account.save()

    if 'mobile' in newData:
        account.mobile = newData['mobile']
        account.updatedAt = datetime.datetime.now(datetime.timezone.utc)
        account.save()
        
    return True

def changePassword(userId, password):
    user = User.objects.get(id=userId)
    if user is None:
        return {"message":"User does not exist"}
    passwordHash = ph.hash(password)
    user.password = passwordHash
    user.save()
    return {"message":"Password updated successfully"}

def forgotPassword(requestData):
    try:
        user = User.objects.get(email=requestData['email'])
    except User.DoesNotExist:
        return {"message":"User does not exist"}

    new_password = generate_random_password()  
    password_hash = ph.hash(new_password)  
    user.password = password_hash
    user.save()
    
    emailService.send_password_reset_email(user.email, new_password)
    
    return {
        "message": "Password reset successfully. Please check your email for the new password.",
    }

def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password