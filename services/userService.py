from bson import ObjectId
from models.common import Account, DatabaseManager, User

dbManager = DatabaseManager()
dbManager.connect()

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


