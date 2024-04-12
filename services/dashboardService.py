from models.common import DatabaseManager,Expense, toJson
from bson import ObjectId
import datetime

dbManager = DatabaseManager()
dbManager.connect()

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

def getSummaryForHomepage(userId, requestData):
    total_share = 0
    total_owe_amount = 0
    total_owed_amount = 0
    dateRange = getDateTime(requestData)
    personal_expenses_pipeline = [
        {
            "$match": {
                "type": "normal",
                "paidBy": ObjectId(userId),
                "date": { 
                    "$gte": dateRange[0],
                    "$lte": dateRange[1]
                }
            }
        },
        {
            "$group": {
                "_id": "$paidBy",
                "totalAmount": { "$sum": "$amount" }
            }
        }
    ]
    result = list(dbManager.aggregate(Expense,personal_expenses_pipeline))
    if len(result) != 0:
        personal_expenses = float(result[0]['totalAmount'])
    else:
        personal_expenses = float(0)
    other_expenses_pipeline = [
        {
            "$lookup": {
                "from": "share",
                "localField": "shares",
                "foreignField": "_id",
                "as": "shared"
            }
        },
        {
            "$match": {
                "$or": [
                    {
                        "type": {"$in": ["group", "friend", "settle"]},
                        "date": { 
                            "$gte": dateRange[0],
                            "$lte": dateRange[1]
                        },
                        "shared.userId": ObjectId(userId)
                    },
                    {
                        "type": {"$in": ["group", "friend", "settle"]},
                        "date": { 
                            "$gte": dateRange[0],
                            "$lte": dateRange[1]
                        },
                        "paidBy": ObjectId(userId)
                    }
                ]
            }
        },
        {
            "$project": {
                "date": 1,
                "paidBy": 1,
                "type": 1,
                "amount": 1,
                "shared": 1,
                "expenseName": 1
            }
        }
    ]
    result = list(dbManager.aggregate(Expense,other_expenses_pipeline))
    for expense in result:
        has_share = False
        for share in expense['shared']:
            if str(share['userId']) == userId:
                has_share = True
                if expense['type'] != 'settle':
                    total_share += float(share['amount'])
                    if str(expense['paidBy']) == userId:
                        total_owed_amount += expense['amount'] - share['amount']
                    else:
                        total_owe_amount += share['amount']
                if str(expense['paidBy']) != userId and expense['type'] == 'settle':
                    total_owed_amount -= share['amount']
        if not has_share and str(expense['paidBy']) == userId:
            if expense['type'] != 'settle':
                total_owed_amount += expense['amount']
            else:
                total_owe_amount -= expense['amount']

    return {
        'group_expenses': float(total_share),
        'personal_expenses': personal_expenses,
        'total_you_owe': float(total_owe_amount),
        'total_owed_to_you': float(total_owed_amount)
    }
    
def getDashboardChart(userId, requestData):
    dateRange = getDateTime(requestData)
    chart_data_pipelines = [
        {
            "$match": {
                "type": "normal",
                "paidBy": ObjectId(userId),
                "date": { 
                    "$gte": dateRange[0],
                    "$lte": dateRange[1]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "totalCost": {"$sum": "$amount"},
                "categories": {"$addToSet": "$category"},
                "categoryData": {
                    "$push": {
                        "category": "$category",
                        "cost": "$amount"
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
    result = list(dbManager.aggregate(Expense,chart_data_pipelines))
    chart_list = [{key: value for key, value in entry.items() if key != '_id'} for entry in result]
    return chart_list