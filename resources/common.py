
from models.common import JSONSerializer

class CreditorDetail(JSONSerializer):
    def __init__(self, id, name,amount):
        self.id = id
        self.name = name
        self.amount = amount

class EventDue(JSONSerializer):
    def __init__(self, id, debtor,creditorDetails):
        self.id = id
        self.debtor = debtor
        self.creditorDetails= creditorDetails

class EventDueSummary(JSONSerializer):
      def __init__(self,eventDues):
        self.eventDues= eventDues
