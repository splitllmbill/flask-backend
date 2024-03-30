from bson import ObjectId
from models.common import DatabaseManager, Verification
import datetime
from services import userService


from util import generator

dbManager = DatabaseManager()
dbManager.connect()

codeMap = {
    'mobile': ('mobileCode','mobileVerified'),
    'email': ('emailCode','emailVerified'),
    'upiNumber': ('upiNumberCode','upiNumberVerified')
}

def generateVerificationCode(user_id,codeType):
    code = generator.codeGenerate(4)
    query={"userId":ObjectId(user_id)}
    updateVal = {
        "updatedAt": datetime.datetime.now(datetime.UTC)
    }
    updateVal[codeMap[codeType][0]] = code
    # updateVal[codeMap[codeType][1]] = False
    user_verification = dbManager.findOne(Verification,query)
    dbManager.update(user_verification, **updateVal)
    return updateVal

def validateCode(user_id, code, codeType, field):
    query={"userId":ObjectId(user_id)}
    user_verification = dbManager.findOne(Verification,query)
    if codeType == 'mobile':
        if code == user_verification['mobileCode']:
            updateVal = {
                "mobileVerified": True,
                "updatedAt": datetime.datetime.now(datetime.UTC)
            }
            dbManager.update(user_verification, **updateVal)
            userService.updateUserAccount(user_id, {
                'mobile': field
            })
        else:
            return False
    elif codeType == 'email':
        if code == user_verification['emailCode']:
            updateVal = {
                "emailVerified": True,
                "updatedAt": datetime.datetime.now(datetime.UTC)
            }
            dbManager.update(user_verification, **updateVal)
        else:
            return False
    elif codeType == 'upiNumber':
        if code == user_verification['upiNumberCode']:
            updateVal = {
                "upiNumberVerified": True,
                "updatedAt": datetime.datetime.now(datetime.UTC)
            }
            dbManager.update(user_verification, **updateVal)
            userService.updateUserAccount(user_id, {
                'upiNumber': field
            })
        else:
            return False
    else:
        return 'Invalid verification type'
    return True

def checkEmailVerified(userId):
    query={"userId":ObjectId(userId)}
    user_verification = dbManager.findOne(Verification,query)
    if user_verification is None or user_verification.emailVerified is None:
        return False
    return user_verification.emailVerified