from mongoengine import connect
from models.common import Expense  # Adjust path if needed
from dotenv import load_dotenv
import os

load_dotenv()

connect(
    db=os.getenv('DB_NAME'),
    host=os.getenv('DB_URL')
)

restored_count = 0
skipped_count = 0

for expense in Expense.objects():
    try:
        if (not expense.amount or expense.amount == 0) and expense.payShares:
            total = sum(float(ps.amount) for ps in expense.payShares if ps.amount is not None)
            expense.amount = total
            expense.save()
            restored_count += 1
        else:
            skipped_count += 1
    except Exception as e:
        print(f"Error restoring expense {expense.id}: {e}")

print(f"✅ Migration complete: Restored `amount` for {restored_count} expenses, skipped {skipped_count}.")
