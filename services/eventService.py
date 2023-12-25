import numpy
from models.common import DatabaseManager,Event
from datetime import datetime as dt
from resources.common import CreditorDetail,EventDue,EventDueSummary
from bson import ObjectId
from services import expenseService,eventService,shareService,userService
dbManager = DatabaseManager()
dbManager.connect()

def getUserEvents(user_id):
    query={
        "users":user_id
    }
    events = dbManager.findAll(Event,query)
    return events

def getEventDues(event_id):
    query={
        "id":event_id
    }
    event = dbManager.findOne(Event,query)
    if event is None:
        raise Exception(ValueError)
   
    user_balances={}
    for user in event.users:
        user_balances[user.id]=0
    
    expenses=expenseService.getEventExpenses(event.id)
    for expense in expenses:
        payerId =expense.paidBy.id
        shares=shareService.getExpenseShares(expense.id)
        print(shares)
        user_payees = {share.userId.id: [] for share in shares}
        amounts_owed = {share.userId.id: {} for share in shares}
        for share in shares:
            shareAmount = share.amount
            participantId= share.userId.id
            if participantId!=payerId:
                user_balances[participantId] += shareAmount
                user_balances[payerId] -= shareAmount
                user_payees[participantId].append(payerId)
                amounts_owed[participantId][payerId] = amounts_owed[participantId].get(payerId, 0) + shareAmount
    result={}
    userNameMap={}
    for user, debts in amounts_owed.items():
        for payee, amount in debts.items():
            if user not in userNameMap:
                userNameMap[str(user)]=userService.getUserNameById(user)
            if payee not in userNameMap:
                userNameMap[str(payee)]=userService.getUserNameById(payee)
            temp={}
            temp[str(payee)]=amount
            result[str(user)]=temp

    eventDues=[]
    for debtor in result:
        debtorName=userNameMap[str(debtor)]
        creditorDetails=[]
        for creditor in result[debtor]:
            creditorName = userNameMap[str(creditor)]
            amount=result[debtor][creditor]
            creditorDetails.append(CreditorDetail(creditor,creditorName,amount).__dict__)
        eventDues.append(EventDue(debtor,debtorName,creditorDetails).__dict__)
    finalResult=EventDueSummary(eventDues)

    return finalResult


def getEventDuesForUser(event_id,user_id):
    result={"inDebtTo":[],"isOwed":[]}
    eventDuesSummary=getEventDues(event_id)
    print(eventDuesSummary.__dict__)
    userName=userService.getUserNameById(user_id)
    for personInDebt in eventDuesSummary.eventDues:
        if personInDebt["id"] == user_id:
           result["inDebtTo"].append(personInDebt["creditorDetails"])
        else:
            for owedPerson in personInDebt["creditorDetails"]:
                if owedPerson["id"]==user_id:
                    result["isOwed"].append({"id":personInDebt["id"],"name":personInDebt["debtor"],"amount":owedPerson["amount"]})
    return result
               
def saveEvent(user_id,request_data):
    new_event = Event(**request_data)
    if "id" in request_data.keys():
        print("noob:")
        print(request_data)
        event=getEventByID(request_data['id'])
        print("noob:")
        original_set = set(event.users)
        modified_set = set(new_event.users)

        # Find the elements that are in the original set but not in the modified set
        removed_elements = original_set - modified_set

        # Convert the result back to a list
        removed_elements_list = list(removed_elements)
        print("noob:",removed_elements_list)
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

