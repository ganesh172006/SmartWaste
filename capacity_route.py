from pymongo import MongoClient
import math

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")

db = client["smart_waste"]
bins_collection = db["bins"]


TRUCK_CAPACITY = 200


def distance(lat1, lon1, lat2, lon2):

    R = 6371

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# Get priority bins
priority_bins = list(
    bins_collection.find(
        {"current_fill_percent": {"$gte": 80}},
        {"_id": 0}
    )
)


depot = {
    "name": "Depot",
    "latitude": 12.9716,
    "longitude": 77.5946
}


remaining_bins = priority_bins.copy()

trips = []


while remaining_bins:

    current_location = depot
    current_load = 0
    current_trip = ["Depot"]

    while remaining_bins:

        possible_bins = [
            bin_data
            for bin_data in remaining_bins
            if current_load + bin_data["estimated_waste_kg"]
            <= TRUCK_CAPACITY
        ]

        if not possible_bins:
            break

        nearest_bin = min(
            possible_bins,
            key=lambda bin_data: distance(
                current_location["latitude"],
                current_location["longitude"],
                bin_data["location"]["latitude"],
                bin_data["location"]["longitude"]
            )
        )

        current_trip.append(nearest_bin["bin_id"])

        current_load += nearest_bin["estimated_waste_kg"]

        current_location = nearest_bin["location"]

        remaining_bins.remove(nearest_bin)

    current_trip.append("Depot")

    trips.append({
        "route": current_trip,
        "load_kg": current_load
    })


print("\n====================================")
print("   SMART WASTE CAPACITY ROUTING")
print("====================================")

print(f"\nTruck Capacity: {TRUCK_CAPACITY} kg")

for index, trip in enumerate(trips, start=1):

    print(f"\nTRIP {index}")

    print(" → ".join(trip["route"]))

    print(f"Load: {trip['load_kg']} kg")

print("\n====================================")
print(f"Total Trips: {len(trips)}")
print("====================================")