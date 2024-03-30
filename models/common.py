from decimal import Decimal
import os
from mongoengine import Document,DecimalField, StringField, IntField, DateTimeField, ReferenceField, ListField, BinaryField, connect, BooleanField
from mongoengine import connect, disconnect
from dotenv import load_dotenv
from bson import ObjectId, Timestamp, DBRef
from datetime import datetime


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
        account_fields = set(type(document)._fields_ordered)
        filtered_kwargs = {key: value for key, value in kwargs.items() if key in account_fields}
        unknown_fields = set(kwargs.keys()) - account_fields
        if unknown_fields:
            raise ValueError(f"Unknown fields found: {', '.join(unknown_fields)}")

        for key, value in filtered_kwargs.items():
            setattr(document, key, value)
        document.save()

    

    def delete(self, document):
        if document:
            document.delete()

def modifyObj(json_data,key,value):
    if isinstance(value, Decimal):
        json_data[key] = float(value)
    elif isinstance(value, ObjectId):
        if key=="_id":
            key="id"
        json_data[key] = str(value)
    elif isinstance(value, Timestamp):
        json_data[key] = {
            "seconds": value.time,
            "ordinal": value.inc
        }
    elif isinstance(value, DBRef):
        ref_id = value.id
        json_data[key] = f"{ref_id}"
    elif isinstance(value, list) and all(isinstance(item, DBRef) for item in value):
        ref_list = []
        for ref in value:
            ref_collection = ref.collection
            ref_id = ref.id
            if ref_collection == 'share':
                share = Share.objects(id=ref_id).first()
                if share:
                    ref_list.append(toJson(share))
            else:
                ref_list.append(f"{ref_id}")
        json_data[key] = ref_list
    elif isinstance(value, list) and all(isinstance(item, ObjectId) for item in value):
        json_data[key] = [str(item) for item in value]
    elif isinstance(value, list):
        result=[]
        for item in value:
            result.append(toJson(item))
        json_data[key]=result
    elif isinstance(value, datetime):
        json_data[key] = value.isoformat()
    else:
        if value is not None:
            json_data[key] = value
    return json_data
def toJson(obj):
    json_data = {}
    if isinstance(obj,dict):
        for key,value in obj.items():
            json_data=modifyObj(json_data,key,value)
    else:
        for key, value in obj._data.items():
            json_data=modifyObj(json_data,key,value)
    return json_data
    
class User(Document):
    name = StringField(required=True)
    email = StringField(required=True,unique=True)
    password = StringField(required=True)
    token = StringField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    account = ReferenceField('Account')
    uuid = StringField(required=True,unique=True)

class Account(Document):
    userId = ReferenceField('User')
    upiId = StringField()
    upiNumber = IntField()
    mobile = IntField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()

class Referral(Document):
    userId = ReferenceField('User')
    inviteCode = StringField()
    usersReferred = ListField(ReferenceField('User'))
    count = IntField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()

class Verification(Document):
    userId = ReferenceField('User')
    emailVerified = BooleanField(default=False)
    emailCode = StringField()
    mobileVerified = BooleanField(default=False)
    mobileCode = StringField()
    upiNumberVerified = BooleanField(default=False)
    upiNumberCode = StringField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    
class Event(Document):
    users = ListField(ReferenceField('User'))
    eventName = StringField(required=True)
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    createdBy = ReferenceField('User')
    updatedBy = ReferenceField('User')
    expenses = ListField(ReferenceField('Expense'))

class Expense(Document):
    expenseName = StringField(required=True)
    amount = DecimalField(required=True)
    type = StringField(required=True)
    paidBy = ReferenceField('User',required=True)
    shares = ListField(ReferenceField('Share'))
    date = DateTimeField(required=True)
    createdAt = DateTimeField(required=True)
    updatedAt = DateTimeField(required=True)
    createdBy = ReferenceField('User',required=True)
    updatedBy = ReferenceField('User',required=True)
    category = StringField(required=False)   
    eventId = ReferenceField('Event',required=False)

class Share(Document):
    amount = DecimalField(required=True)
    userId = ReferenceField('User')
    eventId = ReferenceField('Event')

class Friends(Document):
    userId = ReferenceField('User')
    friends = ListField(ReferenceField('User'))

class BillImages(Document):
    expenseId = ReferenceField('Expense')
    name = StringField(required=True)
    data = BinaryField(required=True)