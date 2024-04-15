from bson import ObjectId
from models.common import DatabaseManager, Event, Expense, Friends, User
from services import expenseService
from datetime import datetime as dt
from collections import defaultdict

dbManager = DatabaseManager()
dbManager.connect()

def getFriendDetails(user_id, friend_id):
    friend = dbManager.findOne(User,{"id":friend_id})
    user = dbManager.findOne(User,{"id":user_id})
    pipeline = [
        {
            "$match": {
                "userId": ObjectId(user_id),
                "friends": {
                    "$elemMatch": {
                        "$eq": ObjectId(friend_id)
                    }
                }
            }
        }
    ]
    isFriend = list(dbManager.aggregate(Friends,pipeline))
    if len(isFriend) == 0:
        return None

    if friend and user:
        expenses =dbManager.findAll(Expense,{"paidBy__in":[friend,user] ,"type__in":["group","friend","settle"]})
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

            if user_owe > 0 or friend_owe > 0:
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
                "uuid": friend.uuid,
                "name": friend.name,
                "overallOweAmount": float(total_owe_amount),
                "overallWhoOwes": overall_who_owes,
                "expenses": expenses_list
            }

        return friend_json
    else:
        return None

def calculate_owed_amounts(friends, expenses, user_id):
    friend_dues = defaultdict(float)
    friend_set = set(friends)
    for expense in expenses:
        paid_by = expense['paidBy']
        if paid_by in friend_set or paid_by == user_id:
            for share in expense['shares']:
                friend_id = share['userId']
                share_amount = share['amount']
                if paid_by == user_id:
                    if friend_id in friend_set:
                        friend_dues[friend_id] += share_amount
                elif paid_by in friend_set:
                    if friend_id == user_id:
                        friend_dues[paid_by] -= share_amount
    return friend_dues

def get_friend_list(user_id):
    friend_expenses_pipeline = [
        {"$match": {"userId": ObjectId(user_id)}},
        {"$lookup": {
            "from": "expense",
            "let": {"userId": "$userId", "friends": "$friends"},
            "pipeline": [
                {"$match": {
                    "$expr": {
                        "$and": [
                            {"$or": [
                                {"$eq": ["$paidBy", "$$userId"]},
                                {"$in": ["$paidBy", "$$friends"]}
                            ]},
                            {"$in": ["$type", ["settle", "friend", "group"]]}
                        ]
                    }
                }},
                {"$project": {
                    "_id": 0,
                    "paidBy": 1,
                    "shares": 1,
                }}
            ],
            "as": "matchedExpenses"
        }}
    ]

    result = list(dbManager.aggregate(Friends,friend_expenses_pipeline))
    if len(result) == 0:
        return {
            "uuid": '',
            "overallYouOwe": 0,
            "overallYouAreOwed": 0,
            "friendsList": [],
        }
    
    friends = result[0]['friends']
    users = [i for i in friends]
    users.append(ObjectId(user_id))
    query={
        "id__in":users
    }
    user_details = dbManager.findAll(User,query)
    user = [i for i in user_details if i['id'] == ObjectId(user_id)]
    uuid = user[0]['uuid']
    expenses = result[0]['matchedExpenses']
    owed_amounts = calculate_owed_amounts(friends,expenses,ObjectId(user_id))
    friendList = [{'id': user['id'], 'name': user['name'], 'email': user['email'], 'oweAmount': owed_amounts[user['id']]} for user in user_details if user['id'] != ObjectId(user_id)]
    overall_you_owe = sum(amount for amount in owed_amounts.values() if amount < 0)
    overall_you_are_owed = sum(amount for amount in owed_amounts.values() if amount > 0)
    response = {
            "uuid": uuid,
            "overallYouOwe": float(abs(overall_you_owe)),
            "overallYouAreOwed": float(abs(overall_you_are_owed)),
            "friendsList": friendList,
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


def settleUpFriendDues(user_id,friend_id):
    #find events where both user and friend and user are present
    #simply per event and settle
    #simply non group expense and settle
    friend = dbManager.findOne(User,{"id":friend_id})
    user = dbManager.findOne(User,{"id":user_id})
    if friend and user:
        events=dbManager.findAll(Event,{"users__all":[friend,user]})
        for event in events:
            net_amount=0
            expense_ids= [str(expense.id) for expense in event.expenses]
            expenses=dbManager.findAll(Expense,{"id__in":expense_ids,"paidBy__in":[friend,user]})
            for expense in expenses:
                for share in expense.shares:
                    if str(expense.paidBy.id)==user_id and str(share.userId.id)==friend_id:
                        net_amount-=float(share.amount)
                    elif str(expense.paidBy.id)==friend_id and str(share.userId.id)==user_id:
                        net_amount+=float(share.amount)
            if net_amount>0:
                request_data={
                    "expenseName": user.name+" settled up with "+friend.name+"("+str(event.eventName)+")" ,
                    "amount": net_amount,
                    "paidBy": str(user.id),
                    "type":"settle",
                    "eventId": str(event.id),
                    "category":"settle",
                    "shares": [
                        {
                            "userId": str(friend.id),
                            "amount": net_amount
                        },
                    ],
                    "date":dt.utcnow()
                }
                expenseService.createExpense(userId=user_id,requestData=request_data)
        friend_details=getFriendDetails(user_id=user_id,friend_id=friend_id)
        if friend_details["overallWhoOwes"]=="user" and friend_details["overallOweAmount"]!=0:
            net_amount=friend_details["overallOweAmount"]
            request_data={
                "expenseName": user.name+" settled up with "+friend.name,
                "amount": net_amount,
                "paidBy": str(user.id),
                "type":"settle",
                "category":"settle",
                "shares": [
                    {
                        "userId": str(friend.id),
                        "amount": net_amount
                    },
                ],
                "date":dt.utcnow()
            }
            expenseService.createExpense(userId=user_id,requestData=request_data)            
        return { "success": 'true', "message": 'Settled successfully!'}
    else:
        return { "success": 'false', "message": 'Invalid request'}

def getFriendDues(user_id, friend_id):
    friend = dbManager.findOne(User,{"id":friend_id})
    user = dbManager.findOne(User,{"id":user_id})

    if friend and user:
        expenses =dbManager.findAll(Expense,{"paidBy__in":[friend,user] ,"type__in":["group","friend","settle"]})
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
            "id": str(friend.id),
            "oweAmount": float(total_owe_amount),
            "whoOwes": overall_who_owes
        }

        return friend_json
    else:
        return None

def add_friend(user_id, requestData):
    friend_code = requestData.get('friendCode')
    
    # Find the user whose friendCode matches the provided value
    friend_user = User.objects(uuid=friend_code).first()
    if not friend_user:
        return { "message": 'Friend not found!'}

    if user_id == str(friend_user.id):
        return { "message": 'Cannot add yourself as a friend!'}
    
    user_friends = Friends.objects(userId=user_id).first()
    if not user_friends:
        user_friends = Friends(userId=user_id, friends=[])
    if friend_user.id in [friend.id for friend in user_friends.friends]:
        return { "message": 'Existing friend!'}
    user_friends.friends.append(ObjectId(friend_user.id))
    user_friends.save()

    # Retrieve the Friends document for the friend
    friend_friends = Friends.objects(userId=friend_user.id).first()
    if not friend_friends:
        friend_friends = Friends(userId=friend_user.id, friends=[])

    friend_friends.friends.append(ObjectId(user_id))
    friend_friends.save()

    return { "message": 'Friend Added Successfully!'}

def delete_friend(user_id, requestData):
    friend_code = requestData.get('friendCode')
    
    friend_user = User.objects(uuid=friend_code).first()
    if (not friend_user) or (user_id == friend_user.id):
        return { "success": 'false',  "message": 'Invalid request'}
    
    # Check if there are any shared groups
    shared_groups = Event.objects(users__all=[user_id, friend_user.id])
    if shared_groups:
        return { "success": 'false', "message": 'Cannot delete friend. You have shared groups.'}

    # Check if there are any unsettled expenses
    unsettled_expenses = getFriendDues(user_id, friend_user.id)
    if unsettled_expenses["oweAmount"] > 0:
        return { "success": 'false', "message": 'Cannot delete friend. There are unsettled expenses.'}

    user_friends = Friends.objects(userId=user_id).first()

    user_friends.friends = [friend for friend in user_friends.friends if str(friend.id) != str(friend_user.id)]
    user_friends.save()

    friend_friends = Friends.objects(userId=friend_user.id).first()
    if not friend_friends:
        return { "success": 'false', "message": 'Invalid request'}

    friend_friends.friends = [friend for friend in friend_friends.friends if str(friend.id) != user_id]
    friend_friends.save()

    return { "success": 'true', "message": 'Unfriended successfully!'}
