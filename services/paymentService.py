from bson import ObjectId
from models.common import DatabaseManager, PaymentPage, toJson
from datetime import datetime, timedelta, timezone
import string
import secrets


dbManager = DatabaseManager()

def generateLink():
    characters = string.ascii_letters + string.digits  # Unreserved characters in a URL
    return ''.join(secrets.choice(characters) for _ in range(256))


def createPage(userId, requestData):
    upiId = requestData['destination']
    expiry = requestData['expiry']
    amount = requestData['amount']
    note = requestData['note']
    page = PaymentPage()
    page.userId = ObjectId(userId)
    now = datetime.now(timezone.utc)
    page.createdAt = now
    page.expiryAt = now + timedelta(hours=expiry)
    page.link = generateLink()
    page.upiId = upiId
    page.upiLink = 'pay?pa=' + upiId + '&pn=User1&tn=' + note + '&am=' + str(amount) + '&cu=INR'
    page.amount = amount
    page.note = note
    page.save()
    return page

def viewPage(link):
    pipeline = [
        {"$match": {"link": link}},
        {"$lookup": {
            "from": "user",
            "localField": "userId",
            "foreignField": "_id",
            "as": "user"
        }},
        {"$unwind": "$user"},
        {"$project": {
            "_id": 0,
            "upiId": 1,
            "upiLink": 1,
            "amount": 1,
            "note": 1,
            "expiryAt": 1,
            "userName": "$user.name"
        }}
    ]
    page = list(dbManager.aggregate(PaymentPage,pipeline))
    if len(page) == 0:
        return False
    return page[0]

def viewPages(userId):
    query = {
        "userId": ObjectId(userId)
    }
    pages = dbManager.findAll(PaymentPage,query)
    return pages