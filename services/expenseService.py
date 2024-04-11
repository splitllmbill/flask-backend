from models.common import DatabaseManager,Expense,Event, Friends, Share, User, toJson
from datetime import datetime as dt
from bson import ObjectId
from services import expenseService, eventService, shareService, friendService

dbManager = DatabaseManager()
dbManager.connect()

def getExpenseById(expenseId, userId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense, query)
    if expense is None:
        return False
    
    # Populate shares
    shares = []
    for share in expense.shares:
        name = "you" if str(share.userId.id) == userId else dbManager.findOne(User, {"id": share.userId.id}).name
        share_info = {
            "amount": float(share.amount),
            "name": name,
            "id": str(share.id),
            "userId": str(share.userId.id)
        }
        shares.append(share_info)

    # Constructing the expense object
    
    result = {
        "expenseName": expense.expenseName,
        "amount": float(expense.amount),
        "type": expense.type,
        "paidById": str(expense.paidBy.id),
        "paidBy": "you" if str(expense.paidBy.id) == userId else dbManager.findOne(User, {"id": expense.paidBy.id}).name,
        "shares": shares,
        "createdAt": str(expense.createdAt),
        "updatedAt": str(expense.updatedAt),
        "createdBy": "you" if str(expense.createdBy.id) == userId else dbManager.findOne(User, {"id": expense.createdBy.id}).name,
        "updatedBy": "you" if str(expense.updatedBy.id) == userId else dbManager.findOne(User, {"id": expense.updatedBy.id}).name,
        "category": expense.category,
        "date": str(expense.date),
        "id": str(expense.id),
        "eventId": str(expense.eventId.id) if expense and hasattr(expense, 'eventId') and hasattr(expense.eventId, 'id') else ""
    }
    return result

def createExpense(userId, requestData):
    shares = requestData['shares']
    shareTotal=0
    for share in shares:
        shareTotal =shareTotal+share["amount"]

    if requestData['type'] != "normal" and shareTotal != requestData["amount"]:
         raise ValueError("Expense amount not equal to sum of shares")
    del requestData['shares']
    new_shares = []
    for i in shares:
        new_share = Share(**i)
        new_share.save()
        new_shares.append(new_share.id)
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

    return new_expense

def updateExpense(userId, expenseId, requestData):
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
        existing_share_ids = [share.id for share in expense.shares]
        new_share_ids = []
        shares = []
        for share_data in shares_data:
            share = Share(userId=ObjectId(share_data['userId']), amount=share_data['amount'])
            share.save()
            shares.append(share)
            new_share_ids.append(share.id)
        shares_to_delete_ids = list(set(existing_share_ids) - set(new_share_ids))
        for shareId in shares_to_delete_ids:
            deleteQuery = {
                "id": shareId
            }
            share = dbManager.findOne(Share,deleteQuery)
            dbManager.delete(share)
        expense.shares = shares
    dbManager.update(expense, **requestData)
    return 'update'


def deleteExpense(expenseId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense,query)
    for share in expense.shares:
        dbManager.delete(share)
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
        

def getAllExpensesForUser(user_id):
    try:
        user_object_id = ObjectId(user_id)
        query = {
            "paidBy": user_object_id,
            "type": "normal"
        }
        all_expenses = dbManager.findAll(Expense, query)
        return all_expenses
    except Exception as e:
        print(f"Error in getAllExpensesForUser function: {e}")
        raise e

def calculate_group_expenses(userId):
    total_share = 0
    total_owe_amount = 0
    total_owed_amount = 0
    expenses = dbManager.findAll(Expense, {"type": {"$in": ["friend", "group"]}})
    
    for expense in expenses:
        for share in expense.shares:
            if str(share.userId) == userId:
                total_share += float(share.amount)
                if expense.paidBy == userId:
                    total_owe_amount+=share.amount 
                else:
                    total_owed_amount+=share.amount  
    
    return { "total_share" : total_share, "total_owe_amount": total_owe_amount, "total_owed_amount":total_owed_amount }     


def getSummaryForHomepage(userId):
    try:
        personal_expenses = getAllExpensesForUser(userId)
        personal_expenses_sum = 0
        for expense in personal_expenses:
            personal_expenses_sum += expense.amount

        group_expenses_summary = calculate_group_expenses(userId)        

        return {
            'group_expenses': group_expenses_summary["total_share"],
            'personal_expenses': personal_expenses_sum,
            'total_you_owe': group_expenses_summary["total_owe_amount"],
            'total_owed_to_you': group_expenses_summary["total_owed_amount"],
        }
    except Exception as e:
        print(f"Error in getSummary function: {e}")
        raise e