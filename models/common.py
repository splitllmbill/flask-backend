from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField, ListField,connect

connect(db='dummy', host='mongodb+srv://admin:urNZLHKvSpFVbvkm@cluster0.tcjo5lg.mongodb.net/?retryWrites=true&w=majority')

class User(Document):
    _id = StringField(required=True, primary_key=True)
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
