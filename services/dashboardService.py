from models.common import DatabaseManager,Expense, toJson
from bson import ObjectId
import datetime

dbManager = DatabaseManager()
dbManager.connect()

def getSummaryForHomepage(userId, requestData):
    total_share = 0
    total_owe_amount = 0
    total_owed_amount = 0
    date_option = requestData["dateSelected"]
    if date_option:
        date_selected = datetime.datetime.strptime(date_option, "%a %b %d %Y")
    else:
        date_selected = datetime.datetime.min

    personal_expenses_pipeline = [
        {
            "$match": {
                "type": "normal",
                "paidBy": ObjectId(userId),
                "date": { "$gte": date_selected }
            }
        },
        {
            "$group": {
                "_id": "$paidBy",
                "totalAmount": { "$sum": "$amount" }
            }
        }
    ]
    result = list(dbManager.aggregate(Expense,personal_expenses_pipeline))[0]
    personal_expenses = float(result['totalAmount'])

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
                        "date": {"$gte": date_selected},
                        "shared.userId": ObjectId(userId)
                    },
                    {
                        "type": {"$in": ["group", "friend", "settle"]},
                        "date": {"$gte": date_selected},
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
    date_option = requestData["dateSelected"]
    if date_option:
        date_selected = datetime.datetime.strptime(date_option, "%a %b %d %Y")
    else:
        date_selected = datetime.datetime.min
    print(date_selected)
    chart_data_pipelines = [
        {
            "$match": {
                "type": "normal",
                "paidBy": ObjectId(userId),
                "date": { "$gte": date_selected}
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
        }
    ]
    result = list(dbManager.aggregate(Expense,chart_data_pipelines))
    chart_list = [{key: value for key, value in entry.items() if key != '_id'} for entry in result]
    return chart_list