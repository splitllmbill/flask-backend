import numpy
from models.common import DatabaseManager,Event, User, toJson
from datetime import datetime as dt,timezone
from resources.common import CreditorDetail,EventDue,EventDueSummary
from bson import ObjectId
from services import expenseService,eventService,shareService,userService, friendService

dbManager = DatabaseManager()
dbManager.connect()

def getUserEvents(user_id):
    
    events = dbManager.findAll(Event, {"users": user_id})
    overall_you_owe = 0
    overall_owed = 0
    overallOweAmount = 0
    owingPerson = ""
    events_with_dues = []
    for event in events:
        event_id = event["id"]
        event_dues = eventService.getEventDuesForUser(event_id, user_id)
        event_dict = event.to_mongo().to_dict()
        event_dict["dues"] = event_dues
        events_with_dues.append(event_dict)
        overall_you_owe += event_dues["totalDebt"]
        overall_owed += event_dues["totalOwed"]
        overallOweAmount = abs(overall_you_owe-overall_owed)
        owingPerson = "user" if overall_you_owe >= overall_owed else "friend"

    response = {
                "overallOweAmount": float(overallOweAmount),
                "owingPerson": owingPerson,
                "events": [toJson(event) for event in events_with_dues]
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
            "name":user.name
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
    if dues.eventDues:
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
            "id": userId
        })
        friend = dbManager.findOne(User,{"id":id})
        users.append({
            "name": friend.name,
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
                "id": str(user.id)
            }
            users.append(res)
    return users