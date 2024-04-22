from decimal import Decimal
import os
from mongoengine import Document,DecimalField,EmbeddedDocument,EmbeddedDocumentField, StringField, IntField, DateTimeField, ReferenceField, ListField, BinaryField, connect, BooleanField
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

    def findAll(self, model, query={}, sort_field="createdAt", sort_order="-"):
        if sort_field not in model._fields:
            return model.objects(**query)
        return model.objects(**query).order_by(sort_order + sort_field)
    
    def findAllMultiSort(self, model, query={}, sort_fields=[("createdAt", "-")]):
        for field, order in sort_fields:
            if field not in model._fields:
                return model.objects(**query)
        sort_params = [(order + field) for field, order in sort_fields]
        return model.objects(**query).order_by(*sort_params)

    def findOne(self, model, query={}):
        return model.objects(**query).first()
    
    def findDistinct(self, model, field, query=None):
        query_set = model.objects
        if query:
            query_set = query_set.filter(query)
        return query_set.distinct(field)

    def update(self, document, **kwargs):
        account_fields = set(type(document)._fields_ordered)
        filtered_kwargs = {key: value for key, value in kwargs.items() if key in account_fields}
        unknown_fields = set(kwargs.keys()) - account_fields
        if unknown_fields:
            raise ValueError(f"Unknown fields found: {', '.join(unknown_fields)}")

        for key, value in filtered_kwargs.items():
            setattr(document, key, value)
        document.save()

    def aggregate(self, model, pipeline):
        return model.objects.aggregate(*pipeline)

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
            ref_id = ref.id
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
    elif isinstance(value,User) or isinstance(value,Account) or isinstance(value,Event): 
        json_data[key] =toJson(value)
    else:
        if value is not None:
            json_data[key] = value
    return json_data
def toJson(obj):
    json_data = {}
    if isinstance(obj,dict):
        for key,value in obj.items():
            json_data=modifyObj(json_data,key,value)
    elif hasattr(obj,"_data"):
        for key, value in obj._data.items():
            json_data=modifyObj(json_data,key,value)
    else:
        return obj
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

class Share(EmbeddedDocument):
    amount = DecimalField(required=True)
    userId = ReferenceField('User')
    eventId = ReferenceField('Event')

class Expense(Document):
    expenseName = StringField(required=True)
    amount = DecimalField(required=True)
    type = StringField(required=True)
    paidBy = ReferenceField('User',required=True)
    shares = ListField(EmbeddedDocumentField(Share))
    date = DateTimeField(required=True)
    createdAt = DateTimeField(required=True)
    updatedAt = DateTimeField(required=True)
    createdBy = ReferenceField('User',required=True)
    updatedBy = ReferenceField('User',required=True)
    category = StringField(required=False)   
    eventId = ReferenceField('Event',required=False)

class Friends(Document):
    userId = ReferenceField('User')
    friends = ListField(ReferenceField('User'))

class BillImages(Document):
    expenseId = ReferenceField('Expense')
    name = StringField(required=True)
    data = BinaryField(required=True)

class Prompts(Document):
    type = StringField(required=True)
    prompt = StringField(required=True)
    version = IntField(required=True)
    hits = IntField(default=0)
    successHits = IntField(default=0)
    failureHits = IntField(default=0)

class PaymentPage(Document):
    userId = ReferenceField('User')
    upiId = StringField(required=True)
    upiLink = StringField(required=True)
    link = StringField(required=True)
    amount = DecimalField(required=True)
    note = StringField(required=True)
    createdAt = DateTimeField(required=True)
    expiryAt = DateTimeField(required=True)