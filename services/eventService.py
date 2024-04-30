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
        "expenses": {"$ifNull": ["$expenses", []]},  # Ensure 'expenses' field exists with a default value of an empty array
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
                "paidBy": 1,
                "shares": 1
            }}
        ],
        "as": "eventExpenses"
    }},
    {"$unwind": "$eventExpenses"},
    # Add more pipeline stages as needed to process expenses and calculate dues
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
        "expenses": {"$push": "$eventExpenses"},
        "eventUsers": {"$push": "$eventUsers"}
    }}
    ]

    
    events = list(dbManager.aggregate(Event, pipeline))
    print(events)
    eventsList = []
    overallOweAmount = 0
    owingPerson = "user"
    userMap = {}
    sameNameDict = {}
    sameNameList = set()
    for event in events:
        for userList in event["eventUsers"]:
            for user in userList:
                userMap[str(user["_id"])] = user
    userName = userMap[str(user_id)]["name"]
    print(userName)
    for event in events:
        eventDict = {}
        print(list(event))
        eventDict["id"] = str(event["_id"])
        # print("event dict used")
        eventDict["users"] = event["users"]
        eventDict["eventName"] = event["eventName"]
        eventDict["createdAt"] = str(event["createdAt"])
        eventDict["createdBy"] = event["createdBy"]
        eventDict["expenses"] = [str(event["_id"]) for event in event["expenses"]] 
        eventDict["dues"] = {
            "userName": userName,
            "inDebtTo": [],
            "isOwed": [],
            "totalDebt": 0,
            "totalOwed": 0
        }
        print(eventDict["expenses"])
        dueDict = {}
        for expense in event["expenses"]:
            for share in expense["shares"]:
                if userMap[str(share["userId"])]["name"] not in sameNameDict:
                    sameNameDict[userMap[str(share["userId"])]["name"]] = userMap[str(share["userId"])]["email"]
                else:
                    if userMap[str(share["userId"])]["email"] != sameNameDict[userMap[str(share["userId"])]["name"]]:
                        sameNameList.add(userMap[str(share["userId"])]["name"])
                if str(share["userId"]) != str(expense["paidBy"]):
                    if str(user_id) == str(expense["paidBy"]):
                        if str(share["userId"]) not in dueDict:
                            dueDict[str(share["userId"])] = -float(share["amount"])
                        else:
                            dueDict[str(share["userId"])] -= float(share["amount"])
                    else:
                        print("friend paid the expense")
                        if str(share["userId"]) != str(user_id):
                            continue
                        if str(expense["paidBy"]) not in dueDict:
                            dueDict[str(expense["paidBy"])] = float(share["amount"])
                        else:
                            dueDict[str(expense["paidBy"])] += float(share["amount"])
        for due in dueDict:
            name =  userMap[str(due)]["name"]
            if name in sameNameList:
                name = name + " ( " + userMap[str(due)]["email"] + " )"
            if dueDict[due] < 0:
                eventDict["dues"]["isOwed"].append({
                    "id": str(due),
                    "name": name,
                    "amount": float(abs(dueDict[due]))
                })
                eventDict["dues"]["totalOwed"] += float(abs(dueDict[due]))
                overallOweAmount += float(dueDict[due])
            else:
                eventDict["dues"]["inDebtTo"].append({
                    "id": str(due),
                    "name": name,
                    "amount": float(abs(dueDict[due]))
                })
                eventDict["dues"]["totalDebt"] += float(abs(dueDict[due]))
                overallOweAmount += float(dueDict[due])
        eventsList.append(eventDict)
    

    print(toJson(eventsList))
    print(overallOweAmount)
    print(sameNameList)
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
        query={
            "id":event_id
        }
        event = dbManager.findOne(Event,query)
        if event is None:
            raise ValueError("Event not found")

        user_balances = {ObjectId(user.id): 0 for user in event.users}
        expenses = expenseService.getEventExpenses(event.id)
        amounts_owed = {}
        user_payees = {}
        for expense in expenses:
            payer_id = str(expense.paidBy.id)
            shares = expense.shares
            for share in shares:
                share_amount = float(share.amount)
                participant_id = str(share.userId.id)
                if participant_id not in amounts_owed:
                    amounts_owed[participant_id]={}
                if payer_id not in amounts_owed[participant_id]:
                    amounts_owed[participant_id][payer_id]=float(0)
                amounts_owed[participant_id][payer_id]+=share_amount
        result = {}
        user_name_map = {}
        calculated_list=[]
        for participant, debts in amounts_owed.items():
            for payer, amount in debts.items():
                if payer+participant not in calculated_list and participant+payer not in calculated_list:
                    payer_to_participant = 0
                    participant_to_payer = amount
                    reverse_exist=False
                    if payer in amounts_owed:
                        if participant in amounts_owed[payer]:
                            reverse_exist=True
                            payer_to_participant=amounts_owed[payer][participant]
                    net_amount = participant_to_payer - payer_to_participant
                    if net_amount>0:
                        amounts_owed[participant][payer]=net_amount
                        if reverse_exist:
                            amounts_owed[payer][participant]=0
                    elif net_amount<0:
                        if not reverse_exist:
                            amounts_owed[payer]={}
                        amounts_owed[payer][participant]=net_amount*-1
                        amounts_owed[participant][payer]=0
                    else:
                        if reverse_exist:
                            amounts_owed[payer][participant]=0
                        amounts_owed[participant][payer]=0
                    if payer not in user_name_map:
                        user_name_map[payer]= userService.getUserNameById(payer)
                    if participant not in user_name_map:
                        user_name_map[participant]= userService.getUserNameById(participant)
                    calculated_list.append(payer+participant)
        
        event_dues = []
        for debtor in amounts_owed:
            debtor_name = user_name_map[str(debtor)]
            creditor_details = []
            for creditor in amounts_owed[debtor]:
                creditor_name = user_name_map[str(creditor)]
                amount = amounts_owed[debtor][creditor]
                if amount!=0:
                    creditor_details.append(CreditorDetail(creditor, creditor_name, amount).__dict__)
            event_dues.append(EventDue(debtor, debtor_name, creditor_details).__dict__)
        
        final_result = EventDueSummary(event_dues)
    
    except ValueError as ve:
        # Handle the specific exception raised when the event is not found
        return {"error": str(ve)}
    return final_result

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

               
def saveEvent(user_id,request_data):
    new_event = Event(**request_data)
    if "id" in request_data.keys():
        event=getEventByID(request_data['id'])
        original_set = set([str(user['id']) for user in event.users])
        modified_set = set(new_event.users)

        # Find the elements that are in the original set but not in the modified set
        removed_elements = original_set - modified_set
        print("noob")
        # Convert the result back to a list
        removed_elements_list = list(removed_elements)
        if event.createdBy in removed_elements_list:
            raise Exception("cannot remove event creator")    
        for expense in event.expenses:
            if expense.paidBy.i in removed_elements_list:
                raise Exception("user present in expenses")
            for share in expense.shares:
                if share.userId.id in removed_elements_list:
                    raise Exception("user present in shares")

        new_event.updatedBy=ObjectId(user_id)
        new_event.updatedAt= dt.utcnow()
    else:
        new_event.createdBy=ObjectId(user_id)
        new_event.createdAt= dt.utcnow()
    
    for user in new_event.users:
        if user.id != ObjectId(user_id):  
            friendService.add_friend(user_id, { "friendCode": user.uuid})

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