from pymongo import MongoClient
import math

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

db = client["smart_waste"]
bins_collection = db["bins"]


def distance(lat1, lon1, lat2, lon2):
    """
    Calculate approximate distance between two GPS coordinates.
    """
    R = 6371  # Earth radius in km

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

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# Get bins that need collection
priority_bins = list(
    bins_collection.find(
        {"current_fill_percent": {"$gte": 80}},
        {"_id": 0}
    )
)


# Starting point of garbage truck
depot = {
    "name": "Depot",
    "latitude": 12.9716,
    "longitude": 77.5946
}


# Create route
remaining_bins = priority_bins.copy()

current_location = depot
route = []

total_distance = 0


while remaining_bins:

    nearest_bin = min(
        remaining_bins,
        key=lambda bin_data: distance(
            current_location["latitude"],
            current_location["longitude"],
            bin_data["location"]["latitude"],
            bin_data["location"]["longitude"]
        )
    )

    bin_distance = distance(
        current_location["latitude"],
        current_location["longitude"],
        nearest_bin["location"]["latitude"],
        nearest_bin["location"]["longitude"]
    )

    total_distance += bin_distance

    route.append(nearest_bin["bin_id"])

    current_location = nearest_bin["location"]

    remaining_bins.remove(nearest_bin)


# Return to depot
total_distance += distance(
    current_location["latitude"],
    current_location["longitude"],
    depot["latitude"],
    depot["longitude"]
)

print("\n====================================")
print("     SMART WASTE ROUTE")
print("====================================")

print("\nStarting Point:")
print("Depot")

print("\nCollection Order:")

for index, bin_id in enumerate(route, start=1):
    print(f"{index}. {bin_id}")

print("\nReturn:")
print("Depot")

print("\nTotal Distance:")
print(f"{total_distance:.2f} km")

print("====================================")