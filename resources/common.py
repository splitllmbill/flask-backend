from flask_mail import Mail
mail=Mail()
class CreditorDetail:
    def __init__(self, id, name,amount):
        self.id = id
        self.name = name
        self.amount = amount

class EventDue:
    def __init__(self, id, debtor,creditorDetails):
        self.id = id
        self.debtor = debtor
        self.creditorDetails= creditorDetails

class EventDueSummary:
      def __init__(self,eventDues):
        self.eventDues= eventDues

class ExpenseResponse:
      def __init__(self,expenses):
        self.expenses= expenses
