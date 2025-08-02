from models.common import DatabaseManager, Expense
from constants import constants
from mongoengine import Q

dbManager = DatabaseManager()

from mongoengine.queryset.visitor import Q

def getFilterOptions(userId, requestData):
    result = {}
    fields = requestData.get("fields", [])

    for field in fields:
        if field in constants.fieldModelMap["expense"]:
            # Match either in shares.userId or payShares.userId
            query = Q(payShares__userId=userId) | Q(shares__userId=userId)

            temp = dbManager.findDistinct(Expense, field, query)

            # Ensure only strings are lowercased
            lowercase = list(set([
                string.lower() for string in temp
                if isinstance(string, str)
            ]))

            result[field] = lowercase

    return result
