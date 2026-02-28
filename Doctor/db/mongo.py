from pymongo import MongoClient

MONGO_URI = "mongodb+srv://medisyncind_db_user:PtmGCjXES1PkTrqE@medisync.n3nbyqn.mongodb.net/medisync?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)

db = client["medisync"]
