from models.common import DatabaseManager,Expense

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

def createExpense(requestData):
    new_expense = Expense(**requestData)
    new_expense.save()
    return new_expense

def updateExpense(expenseId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense,query)
    
    dbManager.delete(expense)
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


