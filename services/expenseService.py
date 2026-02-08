from models.common import DatabaseManager,Expense,Event, Share, User, toJson,PayShare
from datetime import datetime as dt
from bson import ObjectId
from services import expenseService, shareService

from constants import constants

dbManager = DatabaseManager()

def getExpenseById(expenseId, userId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense, query)
    if expense is None:
        return False

    # Constructing the expense object
    new_shares=[]
    for share in expense.shares:
        new_shares.append({
            "userId": str(share.userId.id),
            "name":str(share.userId.name),
            "email":str(share.userId.email),
            "amount": float(share.amount)
        })
    new_payShares=[]
    
    for payShare in expense.payShares:
        print(str(payShare.userId.id))
        new_payShares.append({
            "userId": str(payShare.userId.id),
            "name": str(dbManager.findOne(User, {"id": payShare.userId.id}).name),
            "email": str(dbManager.findOne(User, {"id": payShare.userId.id}).email),
            "amount": float(payShare.amount)
        })
    result = {
        "expenseName": expense.expenseName,
        "amount": float(expense.amount),
        "type": expense.type,
        "payShares":new_payShares,
        "shares":new_shares,
        "createdAt": str(expense.createdAt),
        "updatedAt": str(expense.updatedAt),
        "createdBy": "you" if str(expense.createdBy.id) == userId else dbManager.findOne(User, {"id": expense.createdBy.id}).name,
        "updatedBy": "you" if str(expense.updatedBy.id) == userId else dbManager.findOne(User, {"id": expense.updatedBy.id}).name,
        "category": expense.category,
        "date": str(expense.date),
        "id": str(expense.id),
        "eventId": str(expense.eventId.id) if expense and hasattr(expense, 'eventId') and hasattr(expense.eventId, 'id') else "None",
        "eventName": str(expense.eventId.eventName) if expense and hasattr(expense, 'eventId') and hasattr(expense.eventId, 'eventName') else "None"
    }
    return result

def createExpense(userId, requestData):
    if requestData["expenseName"] == "" or requestData["category"] == "" or requestData["amount"] == 0:
        return {"message": "There are some missing/invalid fields. Please check your input and try again!", "success": "false"}
    if requestData["type"] != "normal" and (len(requestData["payShares"]) == 0 or len(requestData["shares"]) == 0):
        return {"message": "There are some missing/invalid fields. Please check your input and try again!", "success": "false"}
    shares = requestData['shares']
    shareTotal=0
    new_shares=[]
    for share in shares:
        shareTotal =shareTotal+share["amount"]
        new_shares.append(Share(**share))

    if requestData['type'] != "normal" and shareTotal != requestData["amount"] and abs(shareTotal-requestData['amount']) > 1:
        print(shareTotal,requestData['amount'])
        raise ValueError("Expense amount not equal to sum of shares")
    del requestData['shares']
    new_expense = Expense(**requestData)
    new_expense.shares = new_shares
    new_expense.type=requestData["type"]
    new_expense.createdBy = ObjectId(userId)
    new_expense.updatedBy = ObjectId(userId)
    new_expense.createdAt = dt.utcnow()
    new_expense.updatedAt = dt.utcnow()
    new_expense.category = requestData["category"]
    new_expense.date = requestData["date"]

    new_expense.save()

    return {"message":"Expense created!", "success":"true", "data": toJson(new_expense)}

def updateExpense(userId, expenseId, requestData):
    if requestData["expenseName"] == "" or requestData["category"] == "" or requestData["amount"] == 0:
        return {"message": "There are some missing/invalid fields. Please check your input and try again!", "success": "false"}
    if 'type' not in requestData and (len(requestData["shares"]) == 0):
        return {"message":"There are some missing/invalid field. Please check your input and try again!", "success":"false"}
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense, query)
    if expense is None:
        return False
    requestData['updatedAt'] = dt.utcnow()
    requestData['updatedBy'] = ObjectId(userId)
    
    if 'payShares' in requestData:
        new_payShares = []
        for payShare in requestData['payShares']:
            newPayShare = PayShare(
                userId= ObjectId(payShare["userId"]),
                amount= payShare["amount"]
            )
            new_payShares.append(newPayShare)
        expense.payShares = new_payShares
        requestData["payShares"]=new_payShares
    print(expense.payShares)
    if 'shares' in requestData:
        shares_data = requestData.pop('shares')
        shares = []
        for share_data in shares_data:
            share = Share(userId=ObjectId(share_data['userId']), amount=share_data['amount'])
            shares.append(share)
        expense.shares = shares
        requestData["shares"]=shares
    dbManager.update(expense, **requestData)
    return {"message":'Successfully updated expense', "success":"true"}


def deleteExpense(expenseId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense,query)
    if expense is None:
        return False
    dbManager.delete(expense)
    return {"message":'Successfully deleted expense', "success":"true"}

def getEventExpenses(eventId):
    query = {
        "eventId": ObjectId(eventId)
    }
    expenses = dbManager.findAll(Expense, query)
    return expenses

def getEventExpensesAlongWithUserSummary(userId, eventId):
    expenses = expenseService.getEventExpenses(eventId)
    query = {
        "id": eventId
    }
    event = dbManager.findOne(Event,query)
    expenses_with_summary = []
    # Iterate through expenses
    for expense in expenses:
        summary = shareService.getExpenseShares(userId,expense.id)
        # Create a dictionary containing expense details and user summary
        expense_with_summary = {
            "expenseName": expense.expenseName,
            "expenseId": str(expense.id),
            "expenseDate": str(expense.date),
            "type":expense.type,
            # "paidBy":str(expense.paidBy.name),
            "amount": float(expense.amount),
            "category": expense.category,
            "user_summary": summary
        }
        # Append the dictionary to the list
        expenses_with_summary.append(expense_with_summary)
    # Return the list of expenses with user summary
    result = {
        "eventName": event.eventName,
        "expenses": expenses_with_summary
    }
    return result
        
def getAllExpensesForUser(user_id, request_data):
    try:
        user_object_id = ObjectId(user_id)
        filters = request_data["filters"]

        query = {
            "type": "normal",
            "payShares": {
                "$elemMatch": {
                    "userId": user_object_id
                }
            }
        }

        # Apply filters
        for filter in filters:
            field = filter["field"]
            operator = filter["operator"]
            values = filter["values"]

            if operator == 'IN':
                lowercase_filter = [string.lower() for string in values]
                query[field + constants.operatorMap[operator]] = lowercase_filter

            elif operator == "BTW":
                if values[0] != "MIN":
                    query[field + '__gte'] = float(values[0])
                if values[1] != "MAX":
                    query[field + '__lte'] = float(values[1])

        all_expenses = dbManager.findAllMultiSort(Expense, query, [('date', '-'), ('updatedAt', '-')])
        return all_expenses

    except Exception as e:
        print(f"Error in getAllExpensesForUser function: {e}")
        raise e
