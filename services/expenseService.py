from django.http import JsonResponse
from django.core.serializers import serialize
from models.common import DatabaseManager,Expense,Event, Share
from datetime import datetime as dt
from bson import ObjectId
from mongoengine.queryset.visitor import Q
import os
import django
from resources.common import ExpenseResponse

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FLASK-BACKEND.settings")
# django.setup()

dbManager = DatabaseManager()
dbManager.connect()

def getExpenseById(expenseId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense,query)
    if expense is None:
        return False
    return expense

def createExpense(userId, requestData):
    shares = requestData['shares']
    del requestData['shares']
    new_shares = []
    for i in shares:
        new_share = Share(**i)
        new_share.save()
        new_shares.append(new_share.id)
    new_expense = Expense(**requestData)
    new_expense.shares = new_shares
    new_expense.type=requestData["type"]
    new_expense.paidBy = ObjectId(userId)
    new_expense.createdBy = ObjectId(userId)
    new_expense.updatedBy = ObjectId(userId)
    new_expense.createdAt = dt.utcnow()
    new_expense.updatedAt = dt.utcnow()
    new_expense.category = requestData["category"]

    if requestData['type'] == 'group' and requestData["eventId"]:
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
    return 'delete'

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

def getAllExpensesForUser(user_id):
    try:
        print(user_id)
        user_object_id = ObjectId(user_id)
        print(user_object_id)
        query = {
            "paidBy": user_object_id,
            "type": "normal"
        }
        print(query)
        all_expenses = dbManager.findAll(Expense, query)
        print(all_expenses)
        return all_expenses
    except Exception as e:
        print(f"Error in getAllExpensesForUser function: {e}")
        raise e