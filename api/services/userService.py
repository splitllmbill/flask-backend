from models.common import DatabaseManager, User

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
