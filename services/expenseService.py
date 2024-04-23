from models.common import DatabaseManager,Expense,Event, Share, User, toJson
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
    result = {
        "expenseName": expense.expenseName,
        "amount": float(expense.amount),
        "type": expense.type,
        "paidById": str(expense.paidBy.id),
        "paidBy": "you" if str(expense.paidBy.id) == userId else dbManager.findOne(User, {"id": expense.paidBy.id}).name,
        "paidByEmail":dbManager.findOne(User, {"id": expense.paidBy.id}).email,
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
    if requestData["type"] != "normal" and (requestData["paidBy"] == "" or len(requestData["shares"]) == 0):
        return {"message": "There are some missing/invalid fields. Please check your input and try again!", "success": "false"}
    shares = requestData['shares']
    shareTotal=0
    new_shares=[]
    for share in shares:
        shareTotal =shareTotal+share["amount"]
        new_shares.append(Share(**share))

    if requestData['type'] != "normal" and shareTotal != requestData["amount"]:
         raise ValueError("Expense amount not equal to sum of shares")
    del requestData['shares']
    new_expense = Expense(**requestData)
    new_expense.shares = new_shares
    new_expense.type=requestData["type"]
    if requestData["type"] == "normal":
        new_expense["paidBy"] = ObjectId(userId) 
    else:
        new_expense["paidBy"] = ObjectId(requestData["paidBy"])
    new_expense.createdBy = ObjectId(userId)
    new_expense.updatedBy = ObjectId(userId)
    new_expense.createdAt = dt.utcnow()
    new_expense.updatedAt = dt.utcnow()
    new_expense.category = requestData["category"]
    new_expense.date = requestData["date"]

    if requestData['type'] in ['group','settle'] and ("eventId" in requestData) and requestData["eventId"]!="":
        event = dbManager.findOne(Event, {"id": ObjectId(requestData["eventId"])})
        if event:
            new_expense.eventId = ObjectId(requestData["eventId"])
            new_expense.save()  # Save the new expense first
            event.expenses.append(new_expense)
            event.save()  # Save the event after updating its expenses
        else:
            raise ValueError("Event not found for the provided eventId")
    else:
        new_expense.save()

    return {"message":"Expense created!", "success":"true", "data": toJson(new_expense)}

def updateExpense(userId, expenseId, requestData):
    if requestData["expenseName"] == "" or requestData["category"] == "" or requestData["amount"] == 0:
        return {"message": "There are some missing/invalid fields. Please check your input and try again!", "success": "false"}
    if 'type' not in requestData and (requestData["paidBy"] == "" or len(requestData["shares"]) == 0):
        return {"message":"There are some missing/invalid field. Please check your input and try again!", "success":"false"}
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense, query)
    if expense is None:
        return False
    requestData['paidBy'] = ObjectId(requestData['paidBy'])
    requestData['updatedAt'] = dt.utcnow()
    requestData['updatedBy'] = ObjectId(userId)
    if 'shares' in requestData:
        shares_data = requestData.pop('shares')
        shares = []
        for share_data in shares_data:
            share = Share(userId=ObjectId(share_data['userId']), amount=share_data['amount'])
            shares.append(share)
        expense.shares = shares
    dbManager.update(expense, **requestData)
    return {"message":'Successfully updated expense', "success":"true"}


def deleteExpense(expenseId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense,query)
    if expense.eventId and str(expense.eventId.id)!="":
        query={
            "id":expense.eventId.id
        }
        event = dbManager.findOne(Event,query)
        new_expenses=[]
        for expense in event.expenses:
            if str(expense.id) != expenseId:
                new_expenses.append(expense)
        event.expenses=new_expenses
        event.save()
    if expense is None:
        return False
    dbManager.delete(expense)
    return {"message":'Successfully deleted expense', "success":"true"}

def getEventExpenses(eventId):
    query = {
        "id": eventId
    }
    event = dbManager.findOne(Event,query)
    if event is None:
        raise Exception(ValueError)
    
    expense_ids=[]
    for expense in event.expenses:
        expense_ids.append(str(expense.id))

    query={
        "id__in":expense_ids
    }
    expenses=dbManager.findAll(Expense,query)
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
            "paidBy":str(expense.paidBy.name),
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
        
def getAllExpensesForUser(user_id,request_data):
    try:
        user_object_id = ObjectId(user_id)
        filters =request_data["filters"]
        query = {
            "paidBy": user_object_id,
            "type": "normal"
        }
        for filter in filters:
            if filter["operator"]=='IN':
                lowercase_filter = [string.lower() for string in filter["values"]]
                query[filter["field"]+constants.operatorMap[filter["operator"]]] = lowercase_filter
            elif filter["operator"] == "BTW":
                if filter["values"][0] != "MIN":
                    query[filter["field"] + '__gte'] = float(filter["values"][0])
                if filter["values"][1] != "MAX":
                    query[filter["field"] + '__lte'] = float(filter["values"][1])
        all_expenses = dbManager.findAllMultiSort(Expense, query, [('date','-'),('updatedAt','-')])
        return all_expenses
    except Exception as e:
        print(f"Error in getAllExpensesForUser function: {e}")
        raise e