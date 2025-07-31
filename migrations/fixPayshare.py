from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("DB_URL"))
db = client[os.getenv("DB_NAME")]

expense_collection = db.expense

# Find expenses with old payShares
expenses_with_old_payShares = expense_collection.find({
    "payShares": {
        "$elemMatch": {
            "paidBy": {"$exists": True},
            "payAmount": {"$exists": True}
        }
    }
})

updated_count = 0

for expense in expenses_with_old_payShares:
    new_payShares = []
    updated = False

    for ps in expense.get("payShares", []):
        if "paidBy" in ps and "payAmount" in ps:
            new_ps = {
                "userId": ps["paidBy"],
                "amount": ps["payAmount"]
            }
            new_payShares.append(new_ps)
            updated = True
        else:
            new_payShares.append(ps)

    if updated:
        expense_collection.update_one(
            {"_id": expense["_id"]},
            {"$set": {"payShares": new_payShares}}
        )
        print(f"✅ Fixed payShares for expense: {expense['_id']}")
        updated_count += 1

print(f"\n🎉 Migration complete. Total expenses updated: {updated_count}")
