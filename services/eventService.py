from models.common import DatabaseManager,Event
from services import expenseService,eventService,shareService
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
        print(user.id)
        user_balances[user.id]=0
    
    expenses=expenseService.getEventExpenses(event.id)
    for expense in expenses:
        print("nob",expense.id)
        # print("noob:",expense.to_mongo())
        payerId =expense.paidBy.id
        
        shares=shareService.getExpenseShares(expense.id)
        print(shares)
        user_payees = {share.userId.id: [] for share in shares}
        amounts_owed = {share.userId.id: {} for share in shares}
        for share in shares:
            shareAmount = share.amount
            print("shareamount:",shareAmount)
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
            print("ampunt",amount)
            temp={}
            temp[str(payee)]=amount
            result[str(user)]=temp
       # print(f'{user} owes {amount} to {payee}')
    return result