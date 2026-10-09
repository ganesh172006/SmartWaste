from pymongo import MongoClient


client = MongoClient("mongodb://localhost:27017/")

db = client["smart_waste"]
bins_collection = db["bins"]


bin_id = input("Enter Bin ID: ")
new_fill = float(input("Enter new fill percentage: "))


if new_fill >= 90:
    priority = "CRITICAL"
    score = 100

elif new_fill >= 80:
    priority = "HIGH"
    score = 80

elif new_fill >= 60:
    priority = "MEDIUM"
    score = 60

elif new_fill >= 40:
    priority = "LOW"
    score = 40

else:
    priority = "VERY LOW"
    score = 20


result = bins_collection.update_one(
    {"bin_id": bin_id},
    {
        "$set": {
            "current_fill_percent": new_fill,
            "estimated_waste_kg": new_fill,
            "priority": priority,
            "priority_score": score
        }
    }
)


if result.matched_count == 0:

    print("\nBin not found!")

else:

    print("\n====================================")
    print("       BIN UPDATED SUCCESSFULLY")
    print("====================================")

    print(f"Bin ID       : {bin_id}")
    print(f"Fill Level   : {new_fill}%")
    print(f"Priority     : {priority}")
    print(f"Priority Score: {score}")

    print("====================================")
    