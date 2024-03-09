from models.common import DatabaseManager,Expense,Share

dbManager = DatabaseManager()
dbManager.connect()

def getExpenseShares(userId, expenseId):
    expense = dbManager.findOne(Expense, {"id": expenseId})
    if expense is None:
        raise ValueError("Expense not found")

    share_ids = [str(share.id) for share in expense.shares]
    query = {"id__in": share_ids}
    shares = dbManager.findAll(Share, query)
    user_owe=0
    friends_owe=0

    if str(expense.paidBy.id) == userId:  # Expense paid by the user
        for share in shares:
            if str(share.userId.id) != userId:
                friends_owe += share.amount

    else:  # Expense paid by someone else
        for share in shares:
            if str(share.userId.id) == userId:
                user_owe += share.amount
    summary = {
    "oweAmount": float(abs(user_owe - friends_owe)),
    "owePerson": "user" if user_owe > friends_owe else "friend"
    }
    return summary
