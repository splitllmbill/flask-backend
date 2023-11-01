from models.common import DatabaseManager,Event
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
            temp[userNameMap[str(payee)]]=amount
            result[userNameMap[str(user)]]=temp
    return result