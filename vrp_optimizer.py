from pymongo import MongoClient
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


# ==========================================
# MONGODB CONNECTION
# ==========================================

client = MongoClient("mongodb://localhost:27017/")

db = client["smart_waste"]

bins_collection = db["bins"]


# ==========================================
# TRUCK SETTINGS
# ==========================================

TRUCK_CAPACITY = 200


# ==========================================
# DEPOT
# ==========================================

depot = {
    "name": "Depot",
    "latitude": 12.9716,
    "longitude": 77.5946
}


# ==========================================
# GET PRIORITY BINS
# ==========================================

bins = list(
    bins_collection.find(
        {
            "current_fill_percent": {
                "$gte": 80
            }
        },
        {
            "_id": 0
        }
    )
)


# ==========================================
# LOCATIONS
# ==========================================

locations = [depot]

for bin_data in bins:

    locations.append(
        {
            "name": bin_data["bin_id"],
            "latitude": bin_data["location"]["latitude"],
            "longitude": bin_data["location"]["longitude"]
        }
    )


# ==========================================
# WASTE DEMAND
# ==========================================

demands = [0]

for bin_data in bins:

    demands.append(
        int(bin_data["estimated_waste_kg"])
    )


# ==========================================
# CALCULATE NUMBER OF TRUCKS
# ==========================================

total_waste = sum(demands)

num_trucks = max(
    1,
    int(
        (total_waste + TRUCK_CAPACITY - 1)
        // TRUCK_CAPACITY
    )
)


# ==========================================
# DISTANCE FUNCTION
# ==========================================

def distance_km(point1, point2):

    lat1 = point1["latitude"]
    lon1 = point1["longitude"]

    lat2 = point2["latitude"]
    lon2 = point2["longitude"]

    distance = (
        ((lat1 - lat2) ** 2)
        +
        ((lon1 - lon2) ** 2)
    ) ** 0.5

    return distance * 111


# ==========================================
# CREATE DISTANCE MATRIX
# ==========================================

distance_matrix = []

for from_location in locations:

    row = []

    for to_location in locations:

        distance = distance_km(
            from_location,
            to_location
        )

        row.append(
            int(distance * 1000)
        )

    distance_matrix.append(row)


# ==========================================
# OR-TOOLS ROUTING MANAGER
# ==========================================

manager = pywrapcp.RoutingIndexManager(
    len(locations),
    num_trucks,
    [0] * num_trucks,
    [0] * num_trucks
)


# ==========================================
# ROUTING MODEL
# ==========================================

routing = pywrapcp.RoutingModel(manager)


# ==========================================
# DISTANCE CALLBACK
# ==========================================

def distance_callback(from_index, to_index):

    from_node = manager.IndexToNode(
        from_index
    )

    to_node = manager.IndexToNode(
        to_index
    )

    return distance_matrix[
        from_node
    ][
        to_node
    ]


transit_callback_index = (
    routing.RegisterTransitCallback(
        distance_callback
    )
)


routing.SetArcCostEvaluatorOfAllVehicles(
    transit_callback_index
)


# ==========================================
# WASTE DEMAND CALLBACK
# ==========================================

def demand_callback(from_index):

    from_node = manager.IndexToNode(
        from_index
    )

    return demands[from_node]


demand_callback_index = (
    routing.RegisterUnaryTransitCallback(
        demand_callback
    )
)


# ==========================================
# TRUCK CAPACITY CONSTRAINT
# ==========================================

routing.AddDimensionWithVehicleCapacity(
    demand_callback_index,
    0,
    [TRUCK_CAPACITY] * num_trucks,
    True,
    "Capacity"
)


# ==========================================
# SEARCH PARAMETERS
# ==========================================

search_parameters = (
    pywrapcp.DefaultRoutingSearchParameters()
)

search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy
    .PATH_CHEAPEST_ARC
)


# ==========================================
# SOLVE
# ==========================================

solution = routing.SolveWithParameters(
    search_parameters
)


# ==========================================
# DISPLAY RESULT
# ==========================================

print("\n====================================")
print("       SMART WASTE VRP OPTIMIZER")
print("====================================")

print(
    f"\nTruck Capacity : "
    f"{TRUCK_CAPACITY} kg"
)

print(
    f"Total Waste    : "
    f"{total_waste} kg"
)

print(
    f"Trucks Used    : "
    f"{num_trucks}"
)


if solution:

    total_distance = 0

    for vehicle_id in range(num_trucks):

        index = routing.Start(
            vehicle_id
        )

        route = []

        route_load = 0

        route_distance = 0

        while not routing.IsEnd(index):

            node = manager.IndexToNode(
                index
            )

            route.append(
                locations[node]["name"]
            )

            route_load += demands[node]

            previous_index = index

            index = solution.Value(
                routing.NextVar(index)
            )

            route_distance += (
                routing.GetArcCostForVehicle(
                    previous_index,
                    index,
                    vehicle_id
                )
            )

        route.append("Depot")

        total_distance += route_distance

        print(
            f"\nTRUCK {vehicle_id + 1}"
        )

        print(
            " → ".join(route)
        )

        print(
            f"Load     : "
            f"{route_load} kg"
        )

        print(
            f"Distance : "
            f"{route_distance / 1000:.2f} km"
        )

    print("\n====================================")

    print(
        f"Total Distance : "
        f"{total_distance / 1000:.2f} km"
    )

    print("====================================")

else:

    print("\nNo solution found!")