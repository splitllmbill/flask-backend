import os
from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField, ListField,connect
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
            
class JSONSerializer:
    def to_json(self):
        json_data = {}
        for key, value in self._data.items():
            if isinstance(value, ObjectId):
                json_data[key] = str(value)
            elif isinstance(value, Timestamp):
                json_data[key] = {
                    "seconds": value.time,
                    "ordinal": value.inc
                }
            elif isinstance(value, DBRef):
                ref_collection = value.collection
                ref_id = value.id
                if ref_collection == 'user':
                    user = User.objects(id=ref_id).first()
                    if user:
                        json_data[key] = user.name
                elif ref_collection == 'event':
                    event = Event.objects(id=ref_id).first()
                    if event:
                        json_data[key] = event.eventName
                else:
                    json_data[key] = f"{ref_collection} ({ref_id})"
            elif isinstance(value, list) and all(isinstance(item, DBRef) for item in value):
                ref_list = []
                for ref in value:
                    ref_collection = ref.collection
                    ref_id = ref.id
                    if ref_collection == 'share':
                        share = Share.objects(id=ref_id).first()
                        if share:
                            ref_list.append(share.to_json())
                    else:
                        ref_list.append(f"{ref_collection} ({ref_id})")
                json_data[key] = ref_list
            elif isinstance(value, list) and all(isinstance(item, ObjectId) for item in value):
                json_data[key] = [str(item) for item in value]
            elif isinstance(value, datetime):
                json_data[key] = value.isoformat()
            else:
                if value is not None:
                    json_data[key] = value
        return json_data
    
class User(JSONSerializer,Document):
    name = StringField(required=True)
    email = StringField(required=True,unique=True)
    phoneNumber = IntField()
    password = StringField(required=True)
    token = StringField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    account = ReferenceField('Account')

class Account(JSONSerializer,Document):
    userId = ReferenceField('User')
    upiId = StringField()
    upiNumber = IntField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    
class Event(Document,JSONSerializer):
    users = ListField(ReferenceField('User'))
    eventName = StringField(required=True)
    totalExpense = IntField()
    createdAt = DateTimeField()
    updatedAt = DateTimeField()
    createdBy = ReferenceField('User')
    updatedBy = ReferenceField('User')
    expenses = ListField(ReferenceField('Expense'))

class Expense(JSONSerializer,Document):
    expenseName = StringField(required=True)
    amount = IntField(required=True)
    paidBy = ReferenceField('User',required=True)
    shares = ListField(ReferenceField('Share'))
    createdAt = DateTimeField(required=True)
    updatedAt = DateTimeField(required=True)
    createdBy = ReferenceField('User',required=True)
    updatedBy = ReferenceField('User',required=True)

class Share(Document,JSONSerializer):
    amount = IntField()
    userId = ReferenceField('User')
    eventId = ReferenceField('Event')
