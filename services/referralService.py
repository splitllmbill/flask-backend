from bson import ObjectId
from models.common import DatabaseManager, Referral, toJson

from util import generator
import datetime

dbManager = DatabaseManager()
dbManager.connect()

def generateInviteCode(user_id):
    inviteCode = generator.inviteCodeGenerate(6)
    print(inviteCode,user_id)
    query={"userId":ObjectId(user_id)}
    updateVal = {
        "inviteCode": inviteCode
    }
    user_referral = dbManager.findOne(Referral,query)
    dbManager.update(user_referral, **updateVal)
    

def getUserByInviteCode(inviteCode):
    query = {
        "id": inviteCode
    }
    user = dbManager.findOne(Referral,query)
    if user is None:
        return False
    return user.name