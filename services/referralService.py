from bson import ObjectId
from models.common import DatabaseManager, Referral, toJson

from util import generator
import datetime

dbManager = DatabaseManager()
dbManager.connect()

def generateInviteCode(user_id):
    inviteCode = generator.inviteCodeGenerate(6)
    query={"userId":ObjectId(user_id)}
    updateVal = {
        "inviteCode": inviteCode
    }
    user_referral = dbManager.findOne(Referral,query)
    dbManager.update(user_referral, **updateVal)
    return updateVal

def getUserByInviteCode(inviteCode):
    query = {
        "inviteCode": inviteCode
    }
    user = dbManager.findOne(Referral,query)
    if user is None:
        return False
    return True

def addReferredUser(inviteCode, newUser_id):
    print(inviteCode,newUser_id)
    query = {
        "inviteCode": inviteCode
    }
    user_referral = dbManager.findOne(Referral,query)
    user_referral['usersReferred'].append(newUser_id)
    updateVal = {
        "count": user_referral['count'] + 1,
        "usersReferred": user_referral['usersReferred']
    }
    dbManager.update(user_referral, **updateVal)
    return True