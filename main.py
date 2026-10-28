from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from math import radians, sin, cos, sqrt, atan2, ceil

from ortools.constraint_solver import (
    pywrapcp,
    routing_enums_pb2
)

from prediction import (
    save_bin_history,
    get_bin_history,
    predict_bin_fill
)

from ai_route_optimizer import (
    generate_ai_route_candidates
)

from ai_vrp_optimizer import (
    optimize_ai_routes
)


# =========================================================
# FASTAPI
# =========================================================

load_dotenv()

app = FastAPI(
    title="SmartWaste API",
    description="AI-Driven Smart Waste Collection Route Optimization",
    version="3.0"
)


# =========================================================
# CORS
# =========================================================

# CORS
# Always allow the deployed SmartWaste frontend, and allow FRONTEND_URL
# to override/add the deployed origin through Render environment settings.
# Local origins are included for development.
frontend_url = os.getenv(
    "FRONTEND_URL",
    "https://smartwaste-frontend-ku11.onrender.com",
).strip().rstrip("/")

allowed_origins = {
    "https://smartwaste-frontend-ku11.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}
if frontend_url:
    allowed_origins.add(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MONGODB
# =========================================================

# MongoDB connection:
# Locally, MONGODB_URI is loaded from .env. On Render, set it in
# Service -> Environment. Never silently fall back to localhost in production.
MONGO_URL = os.getenv("MONGODB_URI", "").strip()

# Tolerate accidental wrapping quotes or a copied "MONGODB_URI=" prefix.
if MONGO_URL.startswith("MONGODB_URI="):
    MONGO_URL = MONGO_URL.split("=", 1)[1].strip()
MONGO_URL = MONGO_URL.strip().strip('"').strip("'").strip()

if not MONGO_URL:
    raise RuntimeError(
        "MONGODB_URI is missing or empty. Set the full MongoDB Atlas URI "
        "in your local .env file and in Render -> smartwaste-api -> Environment."
    )

if not MONGO_URL.startswith(("mongodb://", "mongodb+srv://")):
    raise RuntimeError(
        "Invalid MONGODB_URI format. The value must start with "
        "mongodb:// or mongodb+srv://. Check Render -> Environment."
    )

client = MongoClient(
    MONGO_URL,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    appname="SmartWaste",
)

db = client["smart_waste"]
bins_collection = db["bins"]


# =========================================================
# CONSTANTS
# =========================================================

TRUCK_CAPACITY = 200

DEPOT = {
    "name": "Depot",
    "latitude": 12.9716,
    "longitude": 77.5946
}


# =========================================================
# REQUEST MODELS
# =========================================================

class FillUpdate(BaseModel):
    fill_percent: float = Field(
        ge=0,
        le=100,
        description="Bin fill percentage between 0 and 100"
    )


# =========================================================
# DISTANCE FUNCTION
# =========================================================

def distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    earth_radius = 6371.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        sin(delta_lat / 2) ** 2
        +
        cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return earth_radius * c


# =========================================================
# PRIORITY
# =========================================================

def calculate_priority(fill):

    if fill >= 90:
        return {
            "priority": "CRITICAL",
            "priority_score": 100,
            "status": "CRITICAL"
        }

    elif fill >= 80:
        return {
            "priority": "HIGH",
            "priority_score": 80,
            "status": "HIGH"
        }

    elif fill >= 60:
        return {
            "priority": "MEDIUM",
            "priority_score": 60,
            "status": "MEDIUM"
        }

    elif fill >= 40:
        return {
            "priority": "LOW",
            "priority_score": 40,
            "status": "LOW"
        }

    return {
        "priority": "VERY LOW",
        "priority_score": 20,
        "status": "LOW"
    }


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "SmartWaste API is running",
        "status": "online",
        "version": "3.0"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():

    try:
        client.admin.command("ping")

        return {
            "status": "healthy",
            "mongodb": "connected"
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"MongoDB connection failed: {str(exc)}"
        )


# =========================================================
# GET ALL BINS
# =========================================================

@app.get("/bins")
def get_bins():

    return list(
        bins_collection.find(
            {},
            {"_id": 0}
        )
    )


# =========================================================
# GET PRIORITY BINS
# =========================================================

@app.get("/bins/priority")
def get_priority_bins():

    return list(
        bins_collection.find(
            {
                "current_fill_percent": {
                    "$gte": 80
                }
            },
            {"_id": 0}
        )
    )


# =========================================================
# GET PRIORITY SCORES
# =========================================================

@app.get("/bins/priority-score")
def get_priority_scores():

    return list(
        bins_collection.find(
            {},
            {
                "_id": 0,
                "bin_id": 1,
                "current_fill_percent": 1,
                "priority": 1,
                "priority_score": 1
            }
        )
    )


# =========================================================
# UPDATE BIN FILL
# =========================================================

@app.put("/bins/{bin_id}/fill")
def update_bin_fill(
    bin_id: str,
    data: FillUpdate
):

    bin_data = bins_collection.find_one({
        "bin_id": bin_id
    })

    if not bin_data:
        raise HTTPException(
            status_code=404,
            detail=f"Bin {bin_id} not found"
        )

    fill = float(data.fill_percent)

    capacity = float(
        bin_data.get("capacity_kg", 100)
    )

    estimated_waste = round(
        capacity * fill / 100,
        2
    )

    priority_data = calculate_priority(fill)

    bins_collection.update_one(
        {"bin_id": bin_id},
        {
            "$set": {
                "current_fill_percent": fill,
                "estimated_waste_kg": estimated_waste,
                "priority": priority_data["priority"],
                "priority_score": priority_data["priority_score"],
                "status": priority_data["status"]
            }
        }
    )

    save_bin_history(
        bin_id,
        fill
    )

    return {
        "message": "Bin updated successfully",
        "bin_id": bin_id,
        "current_fill_percent": fill,
        "estimated_waste_kg": estimated_waste,
        "priority": priority_data["priority"],
        "priority_score": priority_data["priority_score"],
        "status": priority_data["status"]
    }


# =========================================================
# BIN HISTORY
# =========================================================

@app.get("/bins/{bin_id}/history")
def bin_history(bin_id: str):

    bin_data = bins_collection.find_one({
        "bin_id": bin_id
    })

    if not bin_data:
        raise HTTPException(
            status_code=404,
            detail=f"Bin {bin_id} not found"
        )

    return {
        "bin_id": bin_id,
        "history": get_bin_history(bin_id)
    }


# =========================================================
# SINGLE BIN PREDICTION
# =========================================================

@app.get("/bins/{bin_id}/prediction")
def bin_prediction(bin_id: str):

    bin_data = bins_collection.find_one({
        "bin_id": bin_id
    })

    if not bin_data:
        raise HTTPException(
            status_code=404,
            detail=f"Bin {bin_id} not found"
        )

    return predict_bin_fill(bin_id)


# =========================================================
# ALL BIN PREDICTIONS
# =========================================================

@app.get("/predictions")
def all_predictions():

    bins = list(
        bins_collection.find(
            {},
            {
                "_id": 0,
                "bin_id": 1
            }
        )
    )

    return [
        predict_bin_fill(item["bin_id"])
        for item in bins
    ]


# =========================================================
# SIMPLE NEAREST-NEIGHBOUR ROUTE
# =========================================================

@app.get("/route")
def get_route():

    bins = list(
        bins_collection.find(
            {
                "current_fill_percent": {
                    "$gte": 80
                }
            },
            {"_id": 0}
        )
    )

    if not bins:
        return {
            "route": ["Depot", "Depot"],
            "distance_km": 0
        }

    remaining = bins.copy()

    current_lat = DEPOT["latitude"]
    current_lon = DEPOT["longitude"]

    route = ["Depot"]
    total_distance = 0

    while remaining:

        nearest_bin = min(
            remaining,
            key=lambda item: distance_km(
                current_lat,
                current_lon,
                item["location"]["latitude"],
                item["location"]["longitude"]
            )
        )

        total_distance += distance_km(
            current_lat,
            current_lon,
            nearest_bin["location"]["latitude"],
            nearest_bin["location"]["longitude"]
        )

        route.append(nearest_bin["bin_id"])

        current_lat = nearest_bin["location"]["latitude"]
        current_lon = nearest_bin["location"]["longitude"]

        remaining.remove(nearest_bin)

    total_distance += distance_km(
        current_lat,
        current_lon,
        DEPOT["latitude"],
        DEPOT["longitude"]
    )

    route.append("Depot")

    return {
        "route": route,
        "distance_km": round(total_distance, 2)
    }


# =========================================================
# CAPACITY-CONSTRAINED GREEDY ROUTE
# =========================================================

@app.get("/capacity-route")
def get_capacity_route():

    bins = list(
        bins_collection.find(
            {
                "current_fill_percent": {
                    "$gte": 80
                }
            },
            {"_id": 0}
        )
    )

    if not bins:
        return {
            "truck_capacity_kg": TRUCK_CAPACITY,
            "trucks_used": 0,
            "routes": []
        }

    remaining = bins.copy()
    routes = []
    truck_number = 1

    while remaining:

        truck_route = ["Depot"]
        truck_load = 0
        truck_distance = 0

        current_lat = DEPOT["latitude"]
        current_lon = DEPOT["longitude"]

        while remaining:

            possible_bins = [
                item for item in remaining
                if (
                    truck_load
                    + float(item.get("estimated_waste_kg", 0))
                    <= TRUCK_CAPACITY
                )
            ]

            if not possible_bins:
                break

            nearest_bin = min(
                possible_bins,
                key=lambda item: distance_km(
                    current_lat,
                    current_lon,
                    item["location"]["latitude"],
                    item["location"]["longitude"]
                )
            )

            truck_distance += distance_km(
                current_lat,
                current_lon,
                nearest_bin["location"]["latitude"],
                nearest_bin["location"]["longitude"]
            )

            truck_route.append(nearest_bin["bin_id"])

            truck_load += float(
                nearest_bin.get("estimated_waste_kg", 0)
            )

            current_lat = nearest_bin["location"]["latitude"]
            current_lon = nearest_bin["location"]["longitude"]

            remaining.remove(nearest_bin)

        truck_distance += distance_km(
            current_lat,
            current_lon,
            DEPOT["latitude"],
            DEPOT["longitude"]
        )

        truck_route.append("Depot")

        routes.append({
            "truck": truck_number,
            "route": truck_route,
            "load_kg": round(truck_load, 2),
            "distance_km": round(truck_distance, 2)
        })

        truck_number += 1

    return {
        "truck_capacity_kg": TRUCK_CAPACITY,
        "trucks_used": len(routes),
        "routes": routes
    }


# =========================================================
# EXISTING OR-TOOLS VRP
# =========================================================

@app.get("/vrp-route")
def get_vrp_route():

    bins = list(
        bins_collection.find(
            {
                "current_fill_percent": {
                    "$gte": 80
                }
            },
            {"_id": 0}
        )
    )

    if not bins:
        return {
            "truck_capacity_kg": TRUCK_CAPACITY,
            "total_waste_kg": 0,
            "trucks_used": 0,
            "total_distance_km": 0,
            "routes": []
        }

    total_waste = sum(
        float(item.get("estimated_waste_kg", 0))
        for item in bins
    )

    number_of_trucks = max(
        1,
        ceil(total_waste / TRUCK_CAPACITY)
    )

    number_of_trucks = min(
        number_of_trucks,
        len(bins)
    )

    locations = [
        (
            DEPOT["latitude"],
            DEPOT["longitude"]
        )
    ]

    names = ["Depot"]
    demands = [0]

    for item in bins:

        locations.append((
            item["location"]["latitude"],
            item["location"]["longitude"]
        ))

        names.append(item["bin_id"])

        demands.append(
            int(round(
                float(item.get("estimated_waste_kg", 0))
            ))
        )

    distance_matrix = []

    for origin in locations:

        row = []

        for destination in locations:

            row.append(
                int(round(
                    distance_km(
                        origin[0],
                        origin[1],
                        destination[0],
                        destination[1]
                    ) * 1000
                ))
            )

        distance_matrix.append(row)

    manager = pywrapcp.RoutingIndexManager(
        len(locations),
        number_of_trucks,
        0
    )

    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):

        origin = manager.IndexToNode(from_index)
        destination = manager.IndexToNode(to_index)

        return distance_matrix[origin][destination]

    distance_callback_index = (
        routing.RegisterTransitCallback(distance_callback)
    )

    routing.SetArcCostEvaluatorOfAllVehicles(
        distance_callback_index
    )

    def demand_callback(index):

        node = manager.IndexToNode(index)
        return demands[node]

    demand_callback_index = (
        routing.RegisterUnaryTransitCallback(demand_callback)
    )

    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        [TRUCK_CAPACITY] * number_of_trucks,
        True,
        "Capacity"
    )

    search_parameters = (
        pywrapcp.DefaultRoutingSearchParameters()
    )

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )

    search_parameters.time_limit.seconds = 5

    solution = routing.SolveWithParameters(search_parameters)

    if solution is None:
        raise HTTPException(
            status_code=500,
            detail="OR-Tools could not find a feasible route"
        )

    routes = []
    total_distance = 0

    for vehicle_id in range(number_of_trucks):

        index = routing.Start(vehicle_id)

        route = ["Depot"]
        route_load = 0
        route_distance = 0

        while not routing.IsEnd(index):

            node = manager.IndexToNode(index)

            next_index = solution.Value(
                routing.NextVar(index)
            )

            next_node = manager.IndexToNode(next_index)

            route_distance += distance_matrix[node][next_node]

            if node != 0:
                route.append(names[node])
                route_load += demands[node]

            index = next_index

        if route_load > 0:

            route.append("Depot")

            distance = round(route_distance / 1000, 2)

            routes.append({
                "truck": vehicle_id + 1,
                "route": route,
                "load_kg": route_load,
                "distance_km": distance
            })

            total_distance += distance

    return {
        "truck_capacity_kg": TRUCK_CAPACITY,
        "total_waste_kg": round(total_waste, 2),
        "trucks_used": len(routes),
        "total_distance_km": round(total_distance, 2),
        "routes": routes
    }


# =========================================================
# NEW AI-DRIVEN OR-TOOLS ROUTE
# =========================================================

@app.get("/ai-vrp-route")
def get_ai_vrp_route():

    bins = list(
        bins_collection.find(
            {},
            {"_id": 0}
        )
    )

    if not bins:
        return {
            "message": "No bins found",
            "truck_capacity_kg": TRUCK_CAPACITY,
            "trucks_used": 0,
            "total_distance_km": 0,
            "candidates": [],
            "routes": []
        }

    try:

        # Step 1: AI ranking
        candidates = generate_ai_route_candidates(
            bins
        )

        # Step 2: Optimize selected bins
        result = optimize_ai_routes(
            candidates
        )

        # Step 3: Return rankings and routes
        result["candidates"] = candidates

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"AI route optimization failed: {str(exc)}"
        )