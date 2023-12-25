from models.common import DatabaseManager,Expense,Share

dbManager = DatabaseManager()
dbManager.connect()

def getExpenseShares(expenseId):
    query = {
        "id": expenseId
    }
    expense = dbManager.findOne(Expense,query)
    if expense is None:
        raise Exception(ValueError)
    
    share_ids=[]
    for share in expense.shares:
        share_ids.append(str(share.id))

    query={
        "id__in":share_ids
    }
    expenses=dbManager.findAll(Share,query)
    return expenses
