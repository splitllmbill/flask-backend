from models.common import DatabaseManager, Expense
from constants import constants

dbManager = DatabaseManager()
dbManager.connect()

def getFilterOptions(requestData):
    result={}
    
    fields=requestData["fields"]
    for field in fields:
        if field in constants.fieldModelMap["expense"]:
            result[field]=dbManager.findDistinct(Expense,field)
    return result
