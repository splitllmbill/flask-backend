from models.common import DatabaseManager,Expense

dbManager = DatabaseManager()
dbManager.connect()

def getExpenseById(expenseId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense,query)
    if expense is None:
        return ''
    return expense

