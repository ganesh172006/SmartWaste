from datetime import datetime, timedelta
from pymongo import MongoClient
import random


# =========================================================
# MONGODB
# =========================================================

client = MongoClient(
    "mongodb://localhost:27017/"
)

db = client["smart_waste"]

bins_collection = db["bins"]

history_collection = db["bin_history"]


# =========================================================
# CLEAR OLD HISTORY
# =========================================================

history_collection.delete_many({})

print("Old history cleared.")


# =========================================================
# GENERATE REALISTIC HISTORY
# =========================================================

for bin_data in bins_collection.find():

    bin_id = bin_data["bin_id"]

    current_fill = float(
        bin_data.get(
            "current_fill_percent",
            50
        )
    )


    # Different bins get different growth rates

    growth_rate = random.uniform(
        1.5,
        4.5
    )


    # Start 10 hours ago

    start_time = (
        datetime.now()
        -
        timedelta(hours=10)
    )


    records = []


    for hour in range(10):

        timestamp = (
            start_time
            +
            timedelta(hours=hour)
        )


        # Calculate historical fill

        historical_fill = (

            current_fill
            -
            growth_rate
            *
            (9 - hour)

        )


        # Add small realistic variation

        historical_fill += random.uniform(
            -1.0,
            1.0
        )


        historical_fill = max(
            5,
            min(
                100,
                historical_fill
            )
        )


        records.append({

            "bin_id":
                bin_id,

            "fill_percent":
                round(
                    historical_fill,
                    2
                ),

            "timestamp":
                timestamp

        })


    history_collection.insert_many(
        records
    )


    print(
        f"Generated history for {bin_id}"
    )


print()
print("====================================")
print("Historical data generation complete")
print("====================================")