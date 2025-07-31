from bson import ObjectId
from models.common import DatabaseManager, Event, Expense, Friends, User
from services import expenseService
from datetime import datetime as dt
from collections import defaultdict
from mongoengine.queryset.visitor import Q

dbManager = DatabaseManager()

def getFriendDetails(user_id, friend_id):
    friend = dbManager.findOne(User, {"id": friend_id})
    user = dbManager.findOne(User, {"id": user_id})

    # Check if they are friends
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
    isFriend = list(dbManager.aggregate(Friends, pipeline))
    if len(isFriend) == 0:
        return None

    if friend and user:

    
        expenses = Expense.objects(
            Q(type__in=["group", "friend", "settle"]) & (
                Q(payShares__userId=friend.id) | Q(payShares__userId=user.id)
            )
        )



        expenses_list = []
        total_friend_owe = 0
        total_user_owe = 0

        for expense in expenses:
            user_owe = 0
            friend_owe = 0

            # Calculate total paid by each
            user_paid = sum(
                float(ps.amount) for ps in expense.payShares if ps.userId == user
            )
            friend_paid = sum(
                float(ps.amount) for ps in expense.payShares if ps.userId == friend
            )
            total_paid = user_paid + friend_paid

            for share in expense.shares:
                share_user_id = str(share.userId.id)

                if share_user_id not in [str(user.id), str(friend.id)]:
                    continue  # ignore other users

                if total_paid == 0:
                    continue  # skip broken records

                if share_user_id == str(user.id):
                    user_owe += float(share.amount) * (friend_paid / total_paid)
                elif share_user_id == str(friend.id):
                    friend_owe += float(share.amount) * (user_paid / total_paid)

            if user_owe > 0 or friend_owe > 0:
                owe_amount = abs(friend_owe - user_owe)
                who_owes = "friend" if friend_owe > user_owe else "user"

                expense_details = {
                    "expenseDate": expense.createdAt.isoformat(),
                    "expenseName": expense.expenseName,
                    "expenseId": str(expense.id),
                    "eventId": str(expense.eventId.id) if expense.eventId else None,
                    "eventName": str(expense.eventId.eventName) if expense.eventId else None,
                    "category": expense.category,
                    "user_summary": {
                        "oweAmount": float(owe_amount),
                        "owePerson": who_owes,
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

    return None

def calculate_owed_amounts(friends, expenses, user_id):
    friend_dues = defaultdict(float)
    friend_set = set(friends)

    for expense in expenses:
        pay_shares = expense.get('payShares', [])
        shares = expense.get('shares', [])

        # Total paid in the expense (for proportion calculation)
        total_paid = sum(float(p['amount']) for p in pay_shares if p.get('userId') is not None)
        if total_paid == 0:
            continue  # skip invalid expenses

        for share in shares:
            participant_id = share.get('userId')
            share_amount = float(share.get('amount', 0))

            for pay_share in pay_shares:
                payer_id = pay_share.get('userId')
                payer_amount = float(pay_share.get('amount', 0))

                # Proportional amount of this share that payer is covering
                payer_contribution = (payer_amount / total_paid) * share_amount

                if payer_id == user_id and participant_id in friend_set:
                    # User paid for a friend
                    friend_dues[participant_id] += payer_contribution
                elif participant_id == user_id and payer_id in friend_set:
                    # Friend paid for the user
                    friend_dues[payer_id] -= payer_contribution

    return friend_dues


def get_friend_list(user_id):
    friend_expenses_pipeline = [
        {"$match": {"userId": ObjectId(user_id)}},
        {"$addFields": {
            "friends": {"$ifNull": ["$friends", []]}  # Default to empty list if no friends
        }},
        {"$lookup": {
            "from": "expense",
            "let": {"userId": "$userId", "friends": "$friends"},
            "pipeline": [
                {"$addFields": {
                    "payShares": {"$ifNull": ["$payShares", []]}
                }},
                {"$match": {
                    "$expr": {
                        "$and": [
                            {
                                "$or": [
                                    {"$in": [ObjectId(user_id), "$payShares.userId"]},
                                    {
                                        "$gt": [
                                            {
                                                "$size": {
                                                    "$setIntersection": ["$payShares.userId", "$$friends"]
                                                }
                                            },
                                            0
                                        ]
                                    }
                                ]
                            },
                            {"$in": ["$type", ["settle", "friend", "group"]]}
                        ]
                    }   
                }},
                {"$project": {
                    "_id": 0,
                    "payShares": 1,
                    "shares": 1,
                }}
            ],

            "as": "matchedExpenses",
        }}
    ]

    result = list(dbManager.aggregate(Friends, friend_expenses_pipeline))
    
    if not result:
        return {
            "uuid": '',
            "overallYouOwe": 0,
            "overallYouAreOwed": 0,
            "friendsList": [],
        }

    friends = result[0]['friends']
    user_ids = friends + [ObjectId(user_id)]

    user_details = dbManager.findAll(User, {"id__in": user_ids})
    user_map = {str(user["id"]): user for user in user_details}
    user_uuid = user_map[str(user_id)]["uuid"]

    expenses = result[0]['matchedExpenses']
    
    # Use updated owed calculation
    friend_dues = defaultdict(float)
    total_paid = {}

    for expense in expenses:
        payShares = expense.get("payShares", [])
        shares = expense.get("shares", [])
        total_paid_amount = sum(float(p['amount']) for p in payShares)

        if total_paid_amount == 0:
            continue

        for share in shares:
            share_user_id = str(share['userId'])
            share_amount = float(share['amount'])

            for pay in payShares:
                payer_id = str(pay['userId'])
                payer_amount = float(pay['amount'])
                proportion = (payer_amount / total_paid_amount) * share_amount

                if share_user_id == user_id and payer_id in [str(fid) for fid in friends]:
                    friend_dues[payer_id] -= proportion
                elif payer_id == user_id and share_user_id in [str(fid) for fid in friends]:
                    friend_dues[share_user_id] += proportion

    # Prepare response
    friendList = []
    overall_you_owe = 0
    overall_you_are_owed = 0

    for friend_id in friends:
        fid = str(friend_id)
        if fid == user_id or fid not in user_map:
            continue

        amount = friend_dues[fid]
        if amount < 0:
            overall_you_owe += abs(amount)
        else:
            overall_you_are_owed += abs(amount)

        friendList.append({
            "id": str(friend_id),
            "name": user_map[fid]["name"],
            "email": user_map[fid]["email"],
            "oweAmount": abs(amount),
            "whoOwes": "friend" if amount > 0 else "user"
        })

    response = {
        "uuid": user_uuid,
        "overallYouOwe": float(overall_you_owe),
        "overallYouAreOwed": float(overall_you_are_owed),
        "friendsList": friendList
    }

    return response

def getNonGroupExpenses(user_id):
    user = dbManager.findOne(User, {"id": user_id})
    if not user:
        return {"error": "User not found"}

    # Use .objects(Q(...)) directly instead of dbManager
    expenses = list(Expense.objects(
        Q(type="friend") & (Q(shares__userId=user.id) | Q(payShares__userId=user.id))
    ))


    userNameMap = {}
    sameName = {}
    friends_map = {}
    friends_data = []
    overall_you_owe = 0
    overall_you_are_owed = 0

    for expense in expenses:
        shares = expense.shares
        payShares = expense.payShares
        total_paid = sum(float(p.amount) for p in payShares) if payShares else 0

        for share in shares:
            share_user_id = str(share.userId.id)
            share_amount = float(share.amount)

            for payShare in payShares:
                payer_id = str(payShare.userId.id)
                pay_amount = float(payShare.amount)

                if total_paid == 0 or payer_id == share_user_id:
                    continue

                proportional_amount = share_amount * (pay_amount / total_paid)

                # Determine friend_id (the "other" person in the transaction)
                if share_user_id == str(user.id):
                    # I owe someone
                    friend_id = payer_id
                    delta = -proportional_amount
                elif payer_id == str(user.id):
                    # Someone owes me
                    friend_id = share_user_id
                    delta = proportional_amount
                else:
                    continue  # Skip if user not involved in this share-pay pair

                friend = dbManager.findOne(User, {"id": friend_id})
                if friend.name not in userNameMap:
                    userNameMap[friend.name] = friend.email
                elif userNameMap[friend.name] != friend.email:
                    sameName[friend.name] = 1

                if friend_id not in friends_map:
                    friends_map[friend_id] = {
                        "amount": delta,
                        "name": friend.name,
                        "email": friend.email
                    }
                else:
                    friends_map[friend_id]["amount"] += delta

    # Format response
    for friend_id in friends_map:
        data = friends_map[friend_id]
        name = data["name"]
        if name in sameName:
            name = f"{name} ( {data['email']} )"

        who_owes = "friend" if data["amount"] > 0 else "user"
        if data["amount"] < 0:
            overall_you_owe += abs(data["amount"])
        else:
            overall_you_are_owed += abs(data["amount"])

        friends_data.append({
            "name": name,
            "id": str(friend_id),
            "oweAmount": abs(data["amount"]),
            "whoOwes": who_owes
        })

    response = {
        "overallYouOwe": float(round(overall_you_owe, 2)),
        "overallYouAreOwed": float(round(overall_you_are_owed, 2)),
        "friendsList": friends_data
    }

    return response

def settleUpFriendDues(user_id, friend_id):
    friend = dbManager.findOne(User, {"id": friend_id})
    user = dbManager.findOne(User, {"id": user_id})

    if not friend or not user:
        return {"success": 'false', "message": 'Invalid request'}

    # 1. Settle for group events
    events = dbManager.findAll(Event, {"users__all": [friend, user]})
    for event in events:
        net_amount = 0
        expense_ids = [expense.id for expense in event.expenses]
        expenses = dbManager.findAll(Expense, {"id__in": expense_ids})

        for expense in expenses:
            payers = [ps.userId.id for ps in expense.payShares]
            if user.id in payers or friend.id in payers:
                total_paid = sum(float(ps.amount) for ps in expense.payShares)
                if total_paid == 0:
                    continue
                for share in expense.shares:
                    proportion = 0
                    for payShare in expense.payShares:
                        if payShare.userId == user and share.userId == friend:
                            proportion -= float(float(share.amount) * (float(payShare.amount) / total_paid))
                        elif payShare.userId == friend and share.userId == user:
                            proportion += float(float(share.amount) * (float(payShare.amount) / total_paid))
                    net_amount += proportion

        if net_amount > 0:
            request_data = {
                "expenseName": f"{user.name} settled up with {friend.name} ({event.eventName})",
                "amount": net_amount,
                "payShares": [{"userId": str(user.id), "amount": net_amount}],
                "type": "settle",
                "eventId": str(event.id),
                "category": "settle",
                "shares": [{"userId": str(friend.id), "amount": net_amount}],
                "date": dt.utcnow()
            }
            expenseService.createExpense(userId=user_id, requestData=request_data)

    # 2. Settle remaining dues (non-group)
    friend_details = getFriendDues(user_id=user_id, friend_id=friend_id)
    if friend_details["whoOwes"] == "user" and friend_details["oweAmount"] != 0:
        net_amount = friend_details["oweAmount"]
        request_data = {
            "expenseName": f"{user.name} settled up with {friend.name}",
            "amount": net_amount,
            "payShares": [{"userId": str(user.id), "amount": net_amount}],
            "type": "settle",
            "category": "settle",
            "shares": [{"userId": str(friend.id), "amount": net_amount}],
            "date": dt.utcnow()
        }
        expenseService.createExpense(userId=user_id, requestData=request_data)

    return {"success": 'true', "message": 'Settled successfully!'}

    friend = dbManager.findOne(User, {"id": friend_id})
    user = dbManager.findOne(User, {"id": user_id})

    if not friend or not user:
        return {"success": 'false', "message": 'Invalid request'}

    # 1. Settle for group events
    events = dbManager.findAll(Event, {"users__all": [friend, user]})
    for event in events:
        net_amount = 0
        expense_ids = [expense.id for expense in event.expenses]
        expenses = dbManager.findAll(Expense, {"id__in": expense_ids})

        for expense in expenses:
            payers = [ps.userId.id for ps in expense.payShares]
            if user.id in payers or friend.id in payers:
                total_paid = sum(float(ps.amount) for ps in expense.payShares)
                if total_paid == 0:
                    continue
                for share in expense.shares:
                    proportion = 0
                    for payShare in expense.payShares:
                        if payShare.userId == user and share.userId == friend:
                            proportion -= float(float(share.amount) * (float(payShare.amount) / total_paid))
                        elif payShare.userId == friend and share.userId == user:
                            proportion += float(float(share.amount) * (float(payShare.amount) / total_paid))
                    net_amount += proportion

        if net_amount > 0:
            request_data = {
                "expenseName": f"{user.name} settled up with {friend.name} ({event.eventName})",
                "amount": net_amount,
                "payShares": [{"userId": str(user.id), "amount": net_amount}],
                "type": "settle",
                "eventId": str(event.id),
                "category": "settle",
                "shares": [{"userId": str(friend.id), "amount": net_amount}],
                "date": dt.utcnow()
            }
            expenseService.createExpense(userId=user_id, requestData=request_data)

    # 2. Settle remaining dues (non-group)
    friend_details = getFriendDues(user_id=user_id, friend_id=friend_id)
    if friend_details["whoOwes"] == "user" and friend_details["oweAmount"] != 0:
        net_amount = friend_details["oweAmount"]
        request_data = {
            "expenseName": f"{user.name} settled up with {friend.name}",
            "amount": net_amount,
            "payShares": [{"userId": str(user.id), "amount": net_amount}],
            "type": "settle",
            "category": "settle",
            "shares": [{"userId": str(friend.id), "amount": net_amount}],
            "date": dt.utcnow()
        }
        expenseService.createExpense(userId=user_id, requestData=request_data)

    return {"success": 'true', "message": 'Settled successfully!'}

def getFriendDues(user_id, friend_id):
    friend = dbManager.findOne(User, {"id": friend_id})
    user = dbManager.findOne(User, {"id": user_id})

    if not friend or not user:
        return None

    expenses = dbManager.findAll(Expense, {"type__in": ["group", "friend", "settle"]})
    total_friend_owe = 0
    total_user_owe = 0

    for expense in expenses:
        user_owe = 0
        friend_owe = 0

        total_paid = sum(float(ps.amount) for ps in expense.payShares) if expense.payShares else 0
        if total_paid == 0:
            continue

        for share in expense.shares:
            share_amount = float(share.amount)

            for payShare in expense.payShares:
                payer_id = payShare.userId.id
                payer_amount = float(payShare.amount)
                proportion = (payer_amount / total_paid) * share_amount

                if share.userId == user and payer_id == friend.id:
                    user_owe += proportion
                elif share.userId == friend and payer_id == user.id:
                    friend_owe += proportion

        if user_owe > 0 or friend_owe > 0:
            owe_amount = abs(friend_owe - user_owe)
            who_owes = "friend" if friend_owe > user_owe else "user"

            if who_owes == "friend":
                total_friend_owe += owe_amount
            else:
                total_user_owe += owe_amount

    total_owe_amount = abs(total_friend_owe - total_user_owe)
    overall_who_owes = "friend" if total_friend_owe > total_user_owe else "user"

    return {
        "name": friend.name,
        "id": str(friend.id),
        "oweAmount": float(total_owe_amount),
        "whoOwes": overall_who_owes
    }


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
