import numpy
from models.common import DatabaseManager,Event, toJson
from datetime import datetime as dt
from resources.common import CreditorDetail,EventDue,EventDueSummary
from bson import ObjectId
from services import expenseService,eventService,shareService,userService
dbManager = DatabaseManager()
dbManager.connect()

def getUserEvents(user_id):
    events = dbManager.findAll(Event, {"users": user_id})
    overall_you_owe = 0
    overall_owed = 0
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
    query={
        "id":event_id
    }
    event = dbManager.findOne(Event,query)
    if event is None:
        raise ValueError("Event not found")

    user_balances = {user.id: 0 for user in event.users}
    expenses = expenseService.getEventExpenses(event.id)
    amounts_owed = {}
    for expense in expenses:
        payer_id = expense.paidBy.id
        shares = expense.shares
        user_payees = {share.userId.id: [] for share in shares}
        amounts_owed = {share.userId.id: {} for share in shares}

        for share in shares:
            share_amount = float(share.amount)
            participant_id = share.userId.id
            if participant_id != payer_id:
                if participant_id in user_balances:
                    user_balances[participant_id] += share_amount
                else:
                    user_balances[participant_id] = share_amount
                user_balances[payer_id] -= share_amount
                user_payees[participant_id].append(payer_id)
                amounts_owed[participant_id][payer_id] = amounts_owed[participant_id].get(payer_id, 0) + share_amount

    result = {}
    user_name_map = {}
    for user, debts in amounts_owed.items():
        for payee, amount in debts.items():
            if user not in user_name_map:
                user_name_map[str(user)] = userService.getUserNameById(user)
            if payee not in user_name_map:
                user_name_map[str(payee)] = userService.getUserNameById(payee)

            temp = {str(payee): amount}
            result[str(user)] = temp

    event_dues = []
    for debtor in result:
        debtor_name = user_name_map[str(debtor)]
        creditor_details = []

        for creditor in result[debtor]:
            creditor_name = user_name_map[str(creditor)]
            amount = result[debtor][creditor]
            creditor_details.append(CreditorDetail(creditor, creditor_name, amount).__dict__)

        event_dues.append(EventDue(debtor, debtor_name, creditor_details).__dict__)

    final_result = EventDueSummary(event_dues)
    return final_result

def getEventDuesForUser(event_id, user_id):
    result = {"inDebtTo": [], "isOwed": [], "totalDebt": 0, "totalOwed": 0}
    try:
        event_dues_summary = getEventDues(event_id)
        user_name = userService.getUserNameById(user_id)

        for person_in_debt in event_dues_summary.eventDues:
            if person_in_debt["id"] == user_id:
                result["inDebtTo"].append(person_in_debt["creditorDetails"])
                result["totalDebt"] += sum(owed_person["amount"] for owed_person in person_in_debt["creditorDetails"])
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
    for expense in event.expenses:
        dbManager.delete(expense)
    dbManager.delete(event)
    return 'Successfully Deleted Event'

               
def saveEvent(user_id,request_data):
    new_event = Event(**request_data)
    if "id" in request_data.keys():
        event=getEventByID(request_data['id'])
        original_set = set(event.users)
        modified_set = set(new_event.users)

        # Find the elements that are in the original set but not in the modified set
        removed_elements = original_set - modified_set

        # Convert the result back to a list
        removed_elements_list = list(removed_elements)
        for expense in event.expenses:
            if expense.paidBy in removed_elements_list:
                raise Exception("user present in expenses")
            for share in expense.shares:
                if share.userId in removed_elements_list:
                    raise Exception("user present in shares")

        new_event.updatedBy=ObjectId(user_id)
        new_event.updatedAt= dt.utcnow()
    else:
        new_event.createdBy=ObjectId(user_id)
        new_event.createdAt= dt.utcnow()
    new_event.save()
    return new_event
