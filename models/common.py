import os
from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField, ListField,connect
from mongoengine import connect, disconnect
from dotenv import load_dotenv

load_dotenv()
class DatabaseManager:
    def __init__(self):
        self.db_name = os.getenv('DB_URL')
        self.host = os.getenv('DB_NAME')
        self.connection = None

    def connect(self):
        print(self.db_name,self.host)
        if not self.connection:
            self.connection = connect(db=self.db_name, host=self.host)
            # self.connection = connect(db=db_name, host=host)
            print('Connection made to Database')

    def disconnect(self):
        if self.connection:
            disconnect()

    def insert_document(self, model, **kwargs):
        document = model(**kwargs)
        document.save()

    def find_documents(self, model, query={}):
        return model.objects(**query)

    def find_document(self, model, query={}):
        return model.objects(**query).first()

    def update_document(self, document, **kwargs):
        for key, value in kwargs.items():
            setattr(document, key, value)
        document.save()

    def delete_document(self, document):
        if document:
            document.delete()

db_manager = DatabaseManager()
print(db_manager.db_name,db_manager.host)
db_manager.connect()
class User(Document):
    name = StringField(required=True)
    email = StringField(required=True)
    phoneNumber = IntField()
    password = StringField(required=True)
    token = StringField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    account = ReferenceField('Account')

class Account(Document):
    _id = StringField(required=True, primary_key=True)
    userId = ReferenceField('User')
    upiId = StringField()
    upiNumber = IntField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    
class Event(Document):
    _id = StringField(required=True, primary_key=True)
    users = ListField(ReferenceField('User'))
    eventName = StringField(required=True)
    totalExpense = IntField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    createdBy = ReferenceField('User')
    updateBy = ReferenceField('User')
    expenses = ListField(ReferenceField('Expense'))

class Expense(Document):
    expenseName = StringField(required=True)
    amount = IntField()
    paidBy = ReferenceField('User')
    shares = ListField(ReferenceField('Share'))
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    createdBy = ReferenceField('User')
    updatedBy = ReferenceField('User')

class Share(Document):
    _id = StringField(required=True, primary_key=True)
    amount = IntField()
    userId = ReferenceField('User')
    eventId = ReferenceField('Event')
