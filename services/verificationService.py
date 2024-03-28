from models.common import DatabaseManager, Verification

dbManager = DatabaseManager()
dbManager.connect()

def getUserByInviteCode(inviteCode):
    query = {
        "id": user_id
    }
    user = dbManager.findOne(User,query)
    if user is None:
        return False
    return user.name