from models.common import DatabaseManager, Event, Expense, Friends, User
from mongoengine import Q

dbManager = DatabaseManager()
dbManager.connect()

def getFriendDetails(user_id, friend_id):
    friend = dbManager.findOne(User,{"id":friend_id})
    user = dbManager.findOne(User,{"id":user_id})

    if friend and user:
        expenses =dbManager.findAll(Expense,{"paidBy__in":[friend,user] ,"type__in":["group","friend"]})
        expenses_list = []
        total_owe_amount = 0
        total_friend_owe = 0
        total_user_owe = 0

        for expense in expenses:
            user_owe = 0
            friend_owe = 0

            for share in expense.shares:
                if share.userId == user and expense.paidBy == friend:
                    user_owe += share.amount
                elif share.userId == friend and expense.paidBy == user:
                    friend_owe += share.amount

            owe_amount = abs(friend_owe - user_owe)
            who_owes = "friend" if friend_owe > user_owe else "user"

            expense_details = {
                "expenseDate": expense.createdAt.isoformat(),
                "expenseName": expense.expenseName,
                "expenseId": str(expense.id),
                "category": expense.category,
                "user_summary": {
                    "oweAmount": float(owe_amount),
                    "whoOwes": who_owes,
                },
                "expenseType": expense.type
            }
            expenses_list.append(expense_details)

            if who_owes == "friend":
                total_friend_owe += owe_amount
            else:
                total_user_owe += owe_amount

        total_owe_amount = abs(total_friend_owe - total_user_owe)

        overall_who_owes = "friend" if total_friend_owe > total_user_owe else "user"

        friend_json = {
            "name": friend.name,
            "overallOweAmount": float(total_owe_amount),
            "overallWhoOwes": overall_who_owes,
            "expenses": expenses_list
        }

        return friend_json
    else:
        return None
    
def get_friend_list(user_id):

    user = dbManager.findOne(User, {"id": user_id})
    if not user:
        return {"error": "User not found"}

    friends_document = dbManager.findOne(Friends, {"userId": user_id})
    if not friends_document:
        return {
        "overallYouOwe": 0,
        "overallYouAreOwed": 0,
        "friendsList": [],
    }

    friend_owe = {}
    overall_you_owe = 0
    overall_you_are_owed = 0

    for friend_ref in friends_document.friends:
        dues = getFriendDues(user_id, friend_ref.id)
        friend_owe[str(friend_ref.id)] = dues

        # Update overall owe amounts
        overall_you_owe += dues["oweAmount"] if dues["whoOwes"] == "user" else 0
        overall_you_are_owed += dues["oweAmount"] if dues["whoOwes"] == "friend" else 0

    response = {
        "overallYouOwe": float(abs(overall_you_owe)),
        "overallYouAreOwed": float(abs(overall_you_are_owed)),
        "friendsList": list(friend_owe.values())
    }

    return response



def getNonGroupExpenses(user_id):
    user = dbManager.findOne(User,{"id":user_id})
    if not user:
        return {"error": "User not found"}
    
    expenses =dbManager.findAll(Expense,{"type":"friend"})
    friends_owe = {}
    overall_you_owe = 0
    overall_you_are_owed = 0
    
    for expense in expenses:
        user_owe = 0
        friend_owe = 0

        for share in expense.shares:
            friend_id = str(share.userId.id)
            friend = dbManager.findOne(User,{"id":friend_id})

            if share.userId == user and expense.paidBy == friend:
                user_owe += float(share.amount)
            elif share.userId == friend and expense.paidBy == user:
                friend_owe += float(share.amount)

        print(friend_owe,user_owe)
        owe_amount = abs(friend_owe - user_owe)
        who_owes = "friend" if friend_owe > user_owe else "user"
        
        if who_owes == "user":
            overall_you_owe += owe_amount
        else:
            overall_you_are_owed += owe_amount

        if friend_id not in friends_owe:
            friends_owe[friend_id] = {
                "name": friend.name,
                "id": str(friend_id),
                "oweAmount": float(owe_amount),
                "whoOwes": who_owes
            }
        else:
            friends_owe[friend_id]["oweAmount"] += owe_amount

    friends_data = list(friends_owe.values())

    response = {
        "overallYouOwe": float(overall_you_owe),
        "overallYouAreOwed": float(overall_you_are_owed),
        "friendsList": friends_data
    }

    return response


def getFriendDues(user_id, friend_id):
    friend = dbManager.findOne(User,{"id":friend_id})
    user = dbManager.findOne(User,{"id":user_id})

    if friend and user:
        expenses =dbManager.findAll(Expense,{"paidBy__in":[friend,user] ,"type__in":["group","friend"]})
        expenses_list = []
        total_owe_amount = 0
        total_friend_owe = 0
        total_user_owe = 0

        for expense in expenses:
            user_owe = 0
            friend_owe = 0

            for share in expense.shares:
                if share.userId == user and expense.paidBy == friend:
                    user_owe += share.amount
                elif share.userId == friend and expense.paidBy == user:
                    friend_owe += share.amount

            owe_amount = abs(friend_owe - user_owe)
            who_owes = "friend" if friend_owe > user_owe else "user"
            if who_owes == "friend":
                total_friend_owe += owe_amount
            else:
                total_user_owe += owe_amount

        total_owe_amount = abs(total_friend_owe - total_user_owe)

        overall_who_owes = "friend" if total_friend_owe > total_user_owe else "user"

        friend_json = {
            "name": friend.name,
            "friendId": str(friend.id),
            "oweAmount": float(total_owe_amount),
            "whoOwes": overall_who_owes
        }

        return friend_json
    else:
        return None
