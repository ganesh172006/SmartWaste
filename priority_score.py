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

print("\n====================================")
print("       BIN PRIORITY ANALYSIS")
print("====================================")

for bin_data in bins:

    fill = bin_data["current_fill_percent"]

    priority, score = calculate_priority(fill)

    print(
        f"\n{bin_data['bin_id']} - "
        f"{bin_data['location']['name']}"
    )

    print(f"Fill Level : {fill}%")
    print(f"Priority   : {priority}")
    print(f"Score      : {score}")

print("\n====================================")