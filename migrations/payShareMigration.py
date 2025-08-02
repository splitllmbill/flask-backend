from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("DB_URL"))
db = client[os.getenv("DB_NAME")]

expenses = db.expense.find({
    "paidBy": {"$exists": True},
    "amount": {"$exists": True}
})

for expense in expenses:
    expense_id = expense["_id"]
    pay_share = {
        "userId": expense["paidBy"],
        "amount": expense["amount"]
    }
    db.expense.update_one(
        {"_id": expense_id},
        {
            "$set": {"payShares": [pay_share]},
            "$unset": {"paidBy": "", "amount": ""}
        }
    )

print("Migration completed!")
