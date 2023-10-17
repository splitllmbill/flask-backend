import json
from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField, ListField,connect
from mongoengine import connect, disconnect

#connect(db='dummy', host='mongodb+srv://username:password@cluster0.tcjo5lg.mongodb.net/?retryWrites=true&w=majority')
class DatabaseManager:
    def __init__(self, db_name='dummy', host='mongodb+srv://admin:urNZLHKvSpFVbvkm@cluster0.tcjo5lg.mongodb.net/?retryWrites=true&w=majority'):
        self.db_name = db_name
        self.host = host
        self.connection = None

    def connect(self):
        if not self.connection:
            self.connection = connect(db=self.db_name, host=self.host)

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

class User(Document):
    name = StringField(required=True)
    email = StringField(required=True)
    phoneNumber = IntField()
    password = StringField(required=True)
    token = StringField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    account = ReferenceField('Account')
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

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
