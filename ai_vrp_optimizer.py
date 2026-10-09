from ortools.constraint_solver import (
    pywrapcp,
    routing_enums_pb2
)

from math import radians, sin, cos, sqrt, atan2


# -----------------------------------------
# CONFIGURATION
# -----------------------------------------

TRUCK_CAPACITY_KG = 200

NUMBER_OF_TRUCKS = 3

DEPOT = {
    "name": "Waste Collection Depot",
    "latitude": 12.9716,
    "longitude": 77.5946
}


# -----------------------------------------
# DISTANCE CALCULATION
# -----------------------------------------

def haversine_distance(lat1, lon1, lat2, lon2):

    earth_radius_km = 6371

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        +
        cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return earth_radius_km * c


# -----------------------------------------
# BUILD DISTANCE MATRIX
# -----------------------------------------

def build_distance_matrix(locations):

    matrix = []

    for origin in locations:

        row = []

        for destination in locations:

            distance = haversine_distance(
                origin["latitude"],
                origin["longitude"],
                destination["latitude"],
                destination["longitude"]
            )

            row.append(
                int(distance * 1000)
            )

        matrix.append(row)

    return matrix


# -----------------------------------------
# AI-BASED ROUTE OPTIMIZATION
# -----------------------------------------

def optimize_ai_routes(candidates):

    # Only collect bins requiring attention.
    # The AI ranking determines which bins qualify.
    selected_bins = [
        item
        for item in candidates
        if (
            item["ai_priority"] in [
                "IMMEDIATE",
                "URGENT",
                "HIGH"
            ]
        )
    ]

    if not selected_bins:

        return {
            "message": "No bins currently require urgent collection.",
            "truck_capacity_kg": TRUCK_CAPACITY_KG,
            "trucks_used": 0,
            "total_distance_km": 0,
            "routes": []
        }

    # Estimate waste from current fill.
    for item in selected_bins:

        item["estimated_waste_kg"] = int(
            item["capacity_kg"]
            * item["current_fill_percent"]
            / 100
        )

    # Sort by AI priority first.
    selected_bins.sort(
        key=lambda item: item["ai_priority_score"],
        reverse=True
    )

    # Create depot + collection locations.
    locations = [DEPOT]

    for item in selected_bins:

        locations.append({
            "name": item.get(
                "location_name",
                item["bin_id"]
            ),
            "latitude": item["latitude"],
            "longitude": item["longitude"]
        })

    distance_matrix = build_distance_matrix(
        locations
    )

    # OR-Tools uses integer distance values.
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix),
        NUMBER_OF_TRUCKS,
        0
    )

    routing = pywrapcp.RoutingModel(
        manager
    )

    # Distance objective.
    def distance_callback(
        from_index,
        to_index
    ):

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

    # Waste collection capacity constraint.
    def demand_callback(index):

        node = manager.IndexToNode(
            index
        )

        if node == 0:
            return 0

        return selected_bins[
            node - 1
        ]["estimated_waste_kg"]

    demand_callback_index = (
        routing.RegisterUnaryTransitCallback(
            demand_callback
        )
    )

    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        [TRUCK_CAPACITY_KG] * NUMBER_OF_TRUCKS,
        True,
        "Capacity"
    )

    # Search configuration.
    search_parameters = (
        pywrapcp.DefaultRoutingSearchParameters()
    )

    search_parameters.first_solution_strategy = (
        routing_enums_pb2
        .FirstSolutionStrategy
        .PATH_CHEAPEST_ARC
    )

    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2
        .LocalSearchMetaheuristic
        .GUIDED_LOCAL_SEARCH
    )

    search_parameters.time_limit.seconds = 5

    solution = routing.SolveWithParameters(
        search_parameters
    )

    if solution is None:

        return {
            "message": (
                "No feasible route found. "
                "Check truck capacity and bin demands."
            ),
            "truck_capacity_kg": TRUCK_CAPACITY_KG,
            "trucks_used": 0,
            "total_distance_km": 0,
            "routes": []
        }

    routes = []

    total_distance_m = 0

    for vehicle_id in range(
        NUMBER_OF_TRUCKS
    ):

        index = routing.Start(
            vehicle_id
        )

        route_bin_ids = ["Depot"]

        route_distance_m = 0
        route_load_kg = 0

        while not routing.IsEnd(index):

            node = manager.IndexToNode(
                index
            )

            next_index = solution.Value(
                routing.NextVar(index)
            )

            next_node = manager.IndexToNode(
                next_index
            )

            route_distance_m += (
                distance_matrix[node][next_node]
            )

            if node != 0:

                bin_data = selected_bins[
                    node - 1
                ]

                route_bin_ids.append(
                    bin_data["bin_id"]
                )

                route_load_kg += (
                    bin_data["estimated_waste_kg"]
                )

            index = next_index

        # Skip unused trucks.
        if len(route_bin_ids) == 1:
            continue

        route_bin_ids.append(
            "Depot"
        )

        total_distance_m += (
            route_distance_m
        )

        routes.append({
            "truck": vehicle_id + 1,
            "route": route_bin_ids,
            "load_kg": route_load_kg,
            "distance_km": round(
                route_distance_m / 1000,
                2
            )
        })

    return {
        "truck_capacity_kg": TRUCK_CAPACITY_KG,
        "total_selected_bins": len(
            selected_bins
        ),
        "trucks_used": len(routes),
        "total_distance_km": round(
            total_distance_m / 1000,
            2
        ),
        "routes": routes
    }