from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["smart_waste"]

bins = db["bins"]

print("Connected to MongoDB successfully!")

print("\nBins in database:")

for bin_data in bins.find({}, {"_id": 0}):
    print(bin_data)

client.close()