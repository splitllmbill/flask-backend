from models.common import DatabaseManager,Expense
from datetime import datetime as dt
from bson import ObjectId

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
    new_expense = Expense(**requestData)
    new_expense.createdAt = dt.utcnow()
    new_expense.updatedAt = dt.utcnow()
    new_expense.createdBy = ObjectId(userId)
    new_expense.updatedBy = ObjectId(userId)
    new_expense.save()
    return new_expense

def updateExpense(expenseId,requestData):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense,query)
    dbManager.update(expense,**requestData)
    return True

def deleteExpense(expenseId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense,query)
    if expense is None:
        return False
    dbManager.delete(expense)
    return True


