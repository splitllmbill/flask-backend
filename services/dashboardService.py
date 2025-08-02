from models.common import DatabaseManager,Expense, User
from bson import ObjectId
import datetime

dbManager = DatabaseManager()

def getDateTime(requestData):
    start = requestData['startDate']
    end = requestData['endDate']
    if start:
        start_dt = datetime.datetime.strptime(start, "%a %b %d %Y")
    else:
        start_dt = datetime.datetime.min
    if end:
        end_dt = datetime.datetime.strptime(end, "%a %b %d %Y")
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
    else:
        end_dt = datetime.datetime.max
    return [start_dt,end_dt]

def groupOweDetails(userId):
    userId = str(userId)  # ensure consistent string comparison

    pipeline = [
        {
            "$match": {
                "type": {"$in": ["group", "friend", "settle"]},
                "shares.userId": ObjectId(userId)
            }
        },
        {
            "$project": {
                "payShares": 1,
                "shares": 1,
                "type": 1
            }
        }
    ]

    result = list(dbManager.aggregate(Expense, pipeline))

    total_owed_amount = 0  # others owe me
    total_owe_amount = 0   # I owe others

    for expense in result:
        shares = expense.get("shares", [])
        payShares = expense.get("payShares", [])
        total_paid = sum(float(p["amount"]) for p in payShares) if payShares else 0

        for share in shares:
            participant_id = str(share["userId"])
            share_amount = float(share["amount"])

            # Distribute this share among all payers proportionally
            for payShare in payShares:
                payer_id = str(payShare["userId"])
                pay_amount = float(payShare["amount"])

                if total_paid == 0:
                    continue

                proportional_amount = share_amount * (pay_amount / total_paid)

                # Skip self-payment
                if payer_id == participant_id:
                    continue

                if participant_id == userId:
                    # I owe this payer
                    total_owe_amount += proportional_amount
                elif payer_id == userId:
                    # Someone owes me
                    total_owed_amount += proportional_amount

    return (round(total_owe_amount, 2), round(total_owed_amount, 2))

    

def getSummaryForHomepage(userId, requestData):
    query = {"id": ObjectId(userId)}
    user = dbManager.findOne(User, query)
    total_share = 0
    dateRange = getDateTime(requestData)

    # Aggregate personal expenses where user paid (from payShares)
    personal_expenses_pipeline = [
        {
            "$match": {
                "type": "normal",
                "payShares.userId": ObjectId(userId),
                "date": {
                    "$gte": dateRange[0],
                    "$lte": dateRange[1]
                }
            }
        },
        {
            "$unwind": "$payShares"
        },
        {
            "$match": {
                "payShares.userId": ObjectId(userId)
            }
        },
        {
            "$group": {
                "_id": "$payShares.userId",
                "totalAmount": { "$sum": "$payShares.payAmount" }
            }
        }
    ]

    result = list(dbManager.aggregate(Expense, personal_expenses_pipeline))
    personal_expenses = float(result[0]['totalAmount']) if result else 0.0

    # Group/friend/settle expenses where the user is involved
    other_expenses_pipeline = [
        {
            "$match": {
                "type": {"$in": ["group", "friend", "settle"]},
                "date": {
                    "$gte": dateRange[0],
                    "$lte": dateRange[1]
                },
                "shares.userId": ObjectId(userId)
            }
        },
        {
            "$project": {
                "payShares": 1,
                "type": 1,
                "shares": 1,
            }
        }
    ]

    result = list(dbManager.aggregate(Expense, other_expenses_pipeline))
    for expense in result:
        for share in expense['shares']:
            if str(share['userId']) == userId and expense['type'] != 'settle':
                total_share += float(share['amount'])

    total_owe_amount, total_owed_amount = groupOweDetails(userId)

    return {
        'group_expenses': float(total_share),
        'personal_expenses': personal_expenses,
        'total_you_owe': float(total_owe_amount),
        'total_owed_to_you': float(total_owed_amount),
        'username': user.name
    }

    
def getDashboardChart(userId, requestData):
    dateRange = getDateTime(requestData)
    
    chart_data_pipelines = [
        {
            "$match": {
                "type": "normal",
                "date": { 
                    "$gte": dateRange[0],
                    "$lte": dateRange[1]
                }
            }
        },
        {
            "$unwind": "$payShares"
        },
        {
            "$match": {
                "payShares.userId": ObjectId(userId)
            }
        },
        {
            "$group": {
                "_id": None,
                "totalCost": {"$sum": "$payShares.amount"},
                "categoryData": {
                    "$push": {
                        "category": "$category",
                        "cost": "$payShares.amount"
                    }
                }
            }
        },
        {
            "$unwind": "$categoryData"
        },
        {
            "$group": {
                "_id": "$categoryData.category",
                "cost": {"$sum": "$categoryData.cost"},
                "noOfTransactions": {"$sum": 1},
                "totalCost": {"$first": "$totalCost"}
            }
        },
        {
            "$project": {
                "category": "$_id",
                "cost": 1,
                "noOfTransactions": 1,
                "percent": {
                    "$multiply": [
                        {"$divide": ["$cost", "$totalCost"]},
                        100
                    ]
                }
            }
        },
        {
            "$sort": {
                "cost": -1
            }
        }
    ]
    
    result = list(dbManager.aggregate(Expense, chart_data_pipelines))
    chart_list = [{key: value for key, value in entry.items() if key != '_id'} for entry in result]
    return chart_list
