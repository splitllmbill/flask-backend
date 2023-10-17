import pymongo

class Database(object):
    URI = "mongodb+srv://username:password@cluster0.tcjo5lg.mongodb.net/?retryWrites=true&w=majority"
    DB= None

    @staticmethod
    def initalize():
        client = pymongo.MongoClient(Database.URI)
        Database.DB = client['dummy']

    @staticmethod
    def insert(collection, data):
        Database.DB[collection].insert(data)
    
    @staticmethod
    def find(collection, query):
        return Database.DB[collection].find(query)

    @staticmethod
    def find_one(collection, query):
        return Database.DB[collection].find_one(query)