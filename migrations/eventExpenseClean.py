from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("DB_URL"))
db = client[os.getenv("DB_NAME")]

event_collection = db.event
expense_collection = db.expense

# Get all valid expense IDs
valid_expense_ids = set(expense["_id"] for expense in expense_collection.find({}, {"_id": 1}))

print(len(valid_expense_ids))
# Iterate through events
events = event_collection.find({"expenses": {"$exists": True, "$ne": []}})

for event in events:
    old_expenses = event.get("expenses", [])
    cleaned_expenses = [eid for eid in old_expenses if eid in valid_expense_ids]

    if len(cleaned_expenses) != len(old_expenses):
        event_collection.update_one(
            {"_id": event["_id"]},
            {"$set": {"expenses": cleaned_expenses}}
        )
        print(f"Updated event {event['_id']}: removed {len(old_expenses) - len(cleaned_expenses)} invalid expense(s)")

print("Expense cleanup complete.")
