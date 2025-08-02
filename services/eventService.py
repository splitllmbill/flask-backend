import numpy
from models.common import DatabaseManager,Event, User, toJson
from datetime import datetime as dt,timezone
from resources.common import CreditorDetail,EventDue,EventDueSummary
from bson import ObjectId
from services import expenseService,eventService,shareService,userService, friendService

dbManager = DatabaseManager()

def getUserEvents(user_id):
    pipeline = [
        {"$match": {"users": ObjectId(user_id)}},
        {"$addFields": {
            "expenses": {"$ifNull": ["$expenses", []]},
            "users": {"$ifNull": ["$users", []]} 
        }},
        {"$lookup": {
            "from": "expense",
            "let": {"expensesIds": "$expenses"},
            "pipeline": [
                {"$match": {
                    "$expr": {
                        "$in": ["$_id", "$$expensesIds"]
                    }
                }},
                {"$project": {
                    "_id": 1,
                    "payShares": 1,
                    "shares": 1
                }}
            ],
            "as": "eventExpenses"
        }},
        {"$lookup": {
            "from": "user",
            "let": {"userIds": "$users"},
            "pipeline": [
                {"$match": {
                    "$expr": {
                        "$in": ["$_id", "$$userIds"]
                    }
                }},
                {"$project": {
                    "_id": 1,
                    "name": 1,
                    "email": 1
                }}
            ],
            "as": "eventUsers"
        }},
        {"$group": {
            "_id": "$_id",
            "eventName": {"$first": "$eventName"},
            "createdAt": {"$first": "$createdAt"},
            "createdBy": {"$first": "$createdBy"},
            "users": {"$first": "$users"},
            "expenses": {"$first": "$eventExpenses"},
            "eventUsers": {"$push": "$eventUsers"}
        }}
    ]

    events = list(dbManager.aggregate(Event, pipeline))
    eventsList = []
    overallOweAmount = 0
    owingPerson = "user"
    userMap = {}
    sameNameDict = {}
    sameNameList = set()

    # Build userMap
    for event in events:
        for userList in event["eventUsers"]:
            for user in userList:
                userMap[str(user["_id"])] = user

    userName = userMap.get(str(user_id), {}).get("name", "You")

    for event in events:
        print(event.get("_id"))
        eventDict = {
            "id": str(event["_id"]),
            "users": event["users"],
            "eventName": event["eventName"],
            "createdAt": str(event["createdAt"]),
            "createdBy": event["createdBy"],
            "expenses": [str(exp["_id"]) for exp in event["expenses"]],
            "dues": {
                "userName": userName,
                "inDebtTo": [],
                "isOwed": [],
                "totalDebt": 0,
                "totalOwed": 0
            }
        }

        dueDict = {}

        for expense in event["expenses"]:
            print(expense.get("_id"))
            shares = expense.get("shares", [])
            payShares = expense.get("payShares", [])
            print(payShares)
            total_paid = sum(float(ps["amount"]) for ps in payShares) if payShares else 0

            for share in shares:
                participant_id = str(share["userId"])
                share_amount = float(share["amount"])

                # Handle sameName detection
                name = userMap.get(participant_id, {}).get("name", "")
                email = userMap.get(participant_id, {}).get("email", "")
                if name:
                    if name not in sameNameDict:
                        sameNameDict[name] = email
                    elif email != sameNameDict[name]:
                        sameNameList.add(name)

                # Skip if self-paying
                for payShare in payShares:
                    payer_id = str(payShare["userId"])
                    payer_amount = float(payShare["amount"])
                    if total_paid == 0:
                        continue

                    proportional_share = share_amount * (payer_amount / total_paid)

                    if participant_id == payer_id:
                        continue

                    if participant_id == str(user_id):
                        dueDict[payer_id] = dueDict.get(payer_id, 0.0) + proportional_share
                    elif payer_id == str(user_id):
                        dueDict[participant_id] = dueDict.get(participant_id, 0.0) - proportional_share

        for due_id, amount in dueDict.items():
            user_data = userMap.get(due_id, {})
            name = user_data.get("name", "Unknown")
            if name in sameNameList:
                name += f" ( {user_data.get('email', '')} )"
            abs_amount = float(abs(amount))

            if amount < 0:
                eventDict["dues"]["isOwed"].append({
                    "id": str(due_id),
                    "name": name,
                    "amount": abs_amount
                })
                eventDict["dues"]["totalOwed"] += abs_amount
                overallOweAmount += amount
            else:
                eventDict["dues"]["inDebtTo"].append({
                    "id": str(due_id),
                    "name": name,
                    "amount": abs_amount
                })
                eventDict["dues"]["totalDebt"] += abs_amount
                overallOweAmount += amount

        eventsList.append(eventDict)

    if overallOweAmount < 0:
        owingPerson = "friend"
        overallOweAmount = abs(overallOweAmount)

    response = {
        "overallOweAmount": float(overallOweAmount),
        "owingPerson": owingPerson,
        "events": [toJson(event) for event in eventsList]
    }

    return response

def getEventDues(event_id):
    try:
        query = {
            "id": event_id
        }
        event = dbManager.findOne(Event, query)
        if event is None:
            raise ValueError("Event not found")

        user_balances = {ObjectId(user.id): 0 for user in event.users}
        expenses = expenseService.getEventExpenses(event.id)
        amounts_owed = {}
        user_name_map = {}
        calculated_list = []

        for expense in expenses:
            shares = expense.shares  # How much each participant owes
            payShares = expense.payShares  # Who paid how much

            for pay_share in payShares:
                payer_id = str(pay_share.userId.id)

                for share in shares:
                    share_amount = float(share.amount)
                    participant_id = str(share.userId.id)

                    if participant_id == payer_id:
                        continue  # Skip self-payment

                    if participant_id not in amounts_owed:
                        amounts_owed[participant_id] = {}

                    if payer_id not in amounts_owed[participant_id]:
                        amounts_owed[participant_id][payer_id] = 0.0

                    # Divide share amount proportionally across payShares
                    total_paid = sum(float(ps.amount) for ps in payShares)
                    payer_ratio = float(pay_share.amount) / total_paid if total_paid != 0 else 0
                    proportional_share = share_amount * payer_ratio

                    amounts_owed[participant_id][payer_id] += proportional_share

        # Resolve net debts
        for participant, debts in amounts_owed.items():
            for payer, amount in debts.items():
                key1 = payer + participant
                key2 = participant + payer
                if key1 not in calculated_list and key2 not in calculated_list:
                    reverse_exist = False
                    payer_to_participant = 0
                    participant_to_payer = amount

                    if payer in amounts_owed and participant in amounts_owed[payer]:
                        reverse_exist = True
                        payer_to_participant = amounts_owed[payer][participant]

                    net_amount = participant_to_payer - payer_to_participant
                    if net_amount > 0:
                        amounts_owed[participant][payer] = net_amount
                        if reverse_exist:
                            amounts_owed[payer][participant] = 0
                    elif net_amount < 0:
                        if not reverse_exist:
                            amounts_owed[payer] = {}
                        amounts_owed[payer][participant] = -net_amount
                        amounts_owed[participant][payer] = 0
                    else:
                        if reverse_exist:
                            amounts_owed[payer][participant] = 0
                        amounts_owed[participant][payer] = 0

                    # Update name cache
                    if payer not in user_name_map:
                        user_name_map[payer] = userService.getUserNameById(payer)
                    if participant not in user_name_map:
                        user_name_map[participant] = userService.getUserNameById(participant)

                    calculated_list.append(key1)

        # Format response
        event_dues = []
        for debtor in amounts_owed:
            debtor_name = user_name_map[str(debtor)]
            creditor_details = []
            for creditor in amounts_owed[debtor]:
                amount = amounts_owed[debtor][creditor]
                if amount != 0:
                    creditor_name = user_name_map[str(creditor)]
                    creditor_details.append(CreditorDetail(creditor, creditor_name, amount).__dict__)
            event_dues.append(EventDue(debtor, debtor_name, creditor_details).__dict__)

        final_result = EventDueSummary(event_dues)
        return final_result

    except ValueError as ve:
        return {"error": str(ve)}

def getEventDuesForUser(event_id, user_id):
    result = {"userName":"","inDebtTo": [], "isOwed": [], "totalDebt": 0, "totalOwed": 0}
    try:
        event_dues_summary = getEventDues(event_id)
        user_name = userService.getUserNameById(user_id)
        result["userName"]=user_name

        # Assuming event_dues_summary is a single object, not iterable
        # Adjust this part based on the structure of event_dues_summary
        if event_dues_summary.eventDues:
            for person_in_debt in event_dues_summary.eventDues:
                if person_in_debt["id"] == user_id:
                    for owed_person in person_in_debt["creditorDetails"]:
                        result["inDebtTo"].append(owed_person)
                        result["totalDebt"] += owed_person["amount"]
                else:
                    for owed_person in person_in_debt["creditorDetails"]:
                        if owed_person["id"] == user_id:
                            result["isOwed"].append(
                                {"id": person_in_debt["id"], "name": person_in_debt["debtor"], "amount": owed_person["amount"]}
                            )
                            result["totalOwed"] += owed_person["amount"]
    except ValueError as ve:
        # Handle the specific exception raised when the event is not found
        return {"error": str(ve)}

    return result



def getEventByID(event_id):
    query={
        "id":event_id
    }
    event = dbManager.findOne(Event,query)
    user_data=[]
    for user in event.users:
        user_data.append({
            "id":user.id,
            "name":user.name,
            "email":user.email
        })
    event.users=user_data
    if event is None:
        raise Exception(ValueError)
    return event

def deleteEvent(event_id):
    query = {
        "id": event_id
    }
    event = dbManager.findOne(Event,query)
    if event is None:
        return False
    dues = eventService.getEventDues(event_id)
    for due in dues.eventDues:
        if due["creditorDetails"] and len(due["creditorDetails"]) > 0:
            return {"message":'Cannot delete event. There are unsettled dues.', "success":"false"}
    else:
        for expense in event.expenses:
            dbManager.delete(expense)
        dbManager.delete(event)
    return {"message":'Successfully deleted event', "success":"true"}

               
def saveEvent(user_id, request_data):
    new_event = Event(**request_data)
    
    if "id" in request_data:
        event = getEventByID(request_data['id'])
        original_set = set(str(user['id']) for user in event.users)
        modified_set = set(new_event.users)

        removed_elements = original_set - modified_set

        if str(event.createdBy) in removed_elements:
            raise Exception("Cannot remove event creator")
        
        for expense in event.expenses:
            # Check payShares
            for pay_share in expense.payShares:
                if str(pay_share.userId.id) in removed_elements:
                    raise Exception("User present in payShares")
            
            # Check shares
            for share in expense.shares:
                if str(share.userId.id) in removed_elements:
                    raise Exception("User present in shares")
        
        new_event.updatedBy = ObjectId(user_id)
        new_event.updatedAt = dt.utcnow()
    else:
        new_event.createdBy = ObjectId(user_id)
        new_event.createdAt = dt.utcnow()

    # Add any new friends
    for user in new_event.users:
        if user.id != ObjectId(user_id):  
            friendService.add_friend(user_id, {"friendCode": user.uuid})

    new_event.save()
    return new_event

def getEventOrFriendUsers(userId,type,id):
    users = []
    if(type=='friend'):
        user = dbManager.findOne(User,{"id":userId})
        users.append({
            "name": user.name,
            "email":user.email,
            "id": userId
        })
        friend = dbManager.findOne(User,{"id":id})
        users.append({
            "name": friend.name,
            "email":friend.email,
            "id": id
        })
    elif type=='event':
        query = {
            "id": id
        }
        event = dbManager.findOne(Event,query)
        if event is None:
            return False
        for user in event.users:
            res = {
                "name": user.name,
                "email":user.email,
                "id": str(user.id)
            }
            users.append(res)
    return users