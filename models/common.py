import os
from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField, ListField,connect
from mongoengine import connect, disconnect
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()
class DatabaseManager:
    def __init__(self):
        self.db_name = os.getenv('DB_NAME')
        self.host = os.getenv('DB_URL')
        self.connection = None

    def connect(self):
        if not self.connection:
            self.connection = connect(host=self.host,db=self.db_name)
            print('Connection made to Database')

    def disconnect(self):
        if self.connection:
            disconnect()

    def save(self, model, **kwargs):
        document = model(**kwargs)
        document.save()

    def findAll(self, model, query={}):
        return model.objects(**query)

    def findOne(self, model, query={}):
        return model.objects(**query).first()

    def update(self, document, **kwargs):
        for key, value in kwargs.items():
            setattr(document, key, value)
        document.save()

    def delete(self, document):
        if document:
            document.delete()
            
class JSONSerializer:
    def to_json(self):
        return {key: str(value) if isinstance(value, ObjectId) else value
                for key, value in self._data.items()}
    
class User(Document,JSONSerializer):
    name = StringField(required=True)
    email = StringField(required=True,unique=True)
    phoneNumber = IntField()
    password = StringField(required=True)
    token = StringField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    account = ReferenceField('Account')

class Account(Document,JSONSerializer):
    _id = StringField(required=True, primary_key=True)
    userId = ReferenceField('User')
    upiId = StringField()
    upiNumber = IntField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    
class Event(Document,JSONSerializer):
    _id = StringField(required=True, primary_key=True)
    users = ListField(ReferenceField('User'))
    eventName = StringField(required=True)
    totalExpense = IntField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    createdBy = ReferenceField('User')
    updateBy = ReferenceField('User')
    expenses = ListField(ReferenceField('Expense'))

class Expense(Document,JSONSerializer):
    expenseName = StringField(required=True)
    amount = IntField()
    paidBy = ReferenceField('User')
    shares = ListField(ReferenceField('Share'))
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    createdBy = ReferenceField('User')
    updatedBy = ReferenceField('User')

class Share(Document,JSONSerializer):
    _id = StringField(required=True, primary_key=True)
    amount = IntField()
    userId = ReferenceField('User')
    eventId = ReferenceField('Event')
