from pymongo import MongoClient

from ai_route_optimizer import (
    generate_ai_route_candidates
)

from ai_vrp_optimizer import (
    optimize_ai_routes
)


client = MongoClient(
    "mongodb://localhost:27017/"
)

db = client["smart_waste"]

bins = list(
    db["bins"].find(
        {},
        {"_id": 0}
    )
)

print("Calculating AI collection priorities...")

candidates = generate_ai_route_candidates(
    bins
)

print("Optimizing truck routes...")

result = optimize_ai_routes(
    candidates
)

print("\n======================================")
print("AI-DRIVEN SMART WASTE ROUTE OPTIMIZER")
print("======================================")

print(
    f"Truck capacity: "
    f"{result['truck_capacity_kg']} kg"
)

print(
    f"Trucks used: "
    f"{result['trucks_used']}"
)

print(
    f"Total distance: "
    f"{result['total_distance_km']} km"
)

for route in result["routes"]:

    print(
        f"\nTruck {route['truck']}"
    )

    print(
        "Route:",
        " -> ".join(
            route["route"]
        )
    )

    print(
        f"Load: {route['load_kg']} kg"
    )

    print(
        f"Distance: {route['distance_km']} km"
    )