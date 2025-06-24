from mongoengine import connect, Document, EmbeddedDocument, StringField, DecimalField, ReferenceField, ListField, EmbeddedDocumentField, DateTimeField
from models.common import Expense, PayShare, User  # Adjust import based on your project structure
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables if needed
connect(
    db=os.getenv('DB_NAME'),
    host=os.getenv('DB_URL')
) # Adjust your DB name and connection details

# Run migration
for expense in Expense.objects():
    if expense.paidBy and expense.amount:
        # Create new PayShare
        new_pay_share = PayShare(
            paidBy=expense.paidBy,
            payAmount=expense.amount
        )

        # Append to payShares list (create if doesn't exist)
        expense.payShares = [new_pay_share]

        # Remove old fields
        expense.amount = None
        expense.paidBy = None

        # Save changes
        expense.save()

print("Migration completed!")
