from models.common import DatabaseManager, Expense
from constants import constants
from mongoengine import Q

dbManager = DatabaseManager()

def getFilterOptions(userId, requestData):
    result={}
    fields=requestData["fields"]
    for field in fields:
        if field in constants.fieldModelMap["expense"]:
            query = Q(paidBy=userId) | Q(shares__userId=userId)
            temp=dbManager.findDistinct(Expense,field,query)
            lowercase = list(set([string.lower() for string in temp]))
            result[field]=lowercase
    return result
