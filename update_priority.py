from pymongo import MongoClient


client = MongoClient("mongodb://localhost:27017/")

db = client["smart_waste"]
bins_collection = db["bins"]


def calculate_priority(fill_percent):

    if fill_percent >= 90:
        return "CRITICAL", 100

    elif fill_percent >= 80:
        return "HIGH", 80

    elif fill_percent >= 60:
        return "MEDIUM", 60

    elif fill_percent >= 40:
        return "LOW", 40

    else:
        return "VERY LOW", 20


bins = bins_collection.find()

for bin_data in bins:

    fill = bin_data["current_fill_percent"]

    priority, score = calculate_priority(fill)

    bins_collection.update_one(
        {"bin_id": bin_data["bin_id"]},
        {
            "$set": {
                "priority": priority,
                "priority_score": score
            }
        }
    )

    print(
        f"{bin_data['bin_id']} updated → "
        f"{priority} ({score})"
    )


print("\nPriority information successfully saved!")
