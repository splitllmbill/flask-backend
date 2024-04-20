from models.common import DatabaseManager,Expense,Share

dbManager = DatabaseManager()

def getExpenseShares(userId, expenseId):
    expense = dbManager.findOne(Expense, {"id": expenseId})
    if expense is None:
        raise ValueError("Expense not found")
    user_owe=0
    friends_owe=0
    if str(expense.paidBy.id) == userId:  # Expense paid by the user
        for share in expense.shares:
            if str(share.userId.id) != userId:
                friends_owe += share.amount

    else:  # Expense paid by someone else
        for share in expense.shares:
            if str(share.userId.id) == userId:
                user_owe += share.amount
    summary = {
    "oweAmount": float(abs(user_owe - friends_owe)),
    "owePerson": "user" if user_owe > friends_owe else "friend"
    }
    return summary
