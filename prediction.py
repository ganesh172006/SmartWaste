
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# =========================================================
# ENVIRONMENT CONFIGURATION
# =========================================================

load_dotenv()

MONGO_URL = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017/"
)

DATABASE_NAME = "smart_waste"

client = MongoClient(
    MONGO_URL,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    appname="SmartWaste"
)

db = client[DATABASE_NAME]

history_collection = db["bin_history"]


# =========================================================
# SAVE BIN HISTORY
# =========================================================

def save_bin_history(bin_id, fill_percent):
    """
    Save a bin's current fill percentage and timestamp.
    """

    fill_percent = float(fill_percent)

    if not 0 <= fill_percent <= 100:
        raise ValueError("Fill percentage must be between 0 and 100.")

    document = {
        "bin_id": str(bin_id),
        "fill_percent": fill_percent,
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None)
    }

    history_collection.insert_one(document)


# =========================================================
# GET BIN HISTORY
# =========================================================

def get_bin_history(bin_id):
    """
    Retrieve historical readings in chronological order.
    """

    return list(
        history_collection.find(
            {"bin_id": str(bin_id)},
            {"_id": 0}
        ).sort("timestamp", 1)
    )


# =========================================================
# LINEAR REGRESSION
# =========================================================

def linear_regression(x_values, y_values):
    """
    Calculate slope and intercept using ordinary least squares.
    """

    n = len(x_values)

    if n < 2 or len(y_values) != n:
        return None, None

    x_mean = sum(x_values) / n
    y_mean = sum(y_values) / n

    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, y_values)
    )

    denominator = sum(
        (x - x_mean) ** 2
        for x in x_values
    )

    if denominator == 0:
        return None, None

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    return slope, intercept


# =========================================================
# PREDICT BIN FILL
# =========================================================

def predict_bin_fill(bin_id):
    """
    Estimate the next-hour fill level, fill rate,
    time to 90% capacity, and overflow risk.

    This is a linear-regression baseline, not a guarantee
    of future fill levels.
    """

    try:
        history = get_bin_history(bin_id)

    except PyMongoError as exc:
        return {
            "bin_id": str(bin_id),
            "prediction_available": False,
            "message": "Unable to retrieve bin history from MongoDB.",
            "current_fill_percent": None,
            "fill_rate_percent_per_hour": None,
            "predicted_fill_next_hour": None,
            "hours_to_90_percent": None,
            "overflow_risk": "UNKNOWN",
            "historical_readings": 0
        }

    # -----------------------------------------------------
    # Validate historical readings
    # -----------------------------------------------------

    valid_history = []

    for record in history:
        timestamp = record.get("timestamp")
        fill_percent = record.get("fill_percent")

        if not isinstance(timestamp, datetime):
            continue

        try:
            fill_percent = float(fill_percent)
        except (TypeError, ValueError):
            continue

        if not 0 <= fill_percent <= 100:
            continue

        # Normalize timezone-aware timestamps.
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(
                timezone.utc
            ).replace(tzinfo=None)

        valid_history.append({
            "timestamp": timestamp,
            "fill_percent": fill_percent
        })

    valid_history.sort(key=lambda item: item["timestamp"])

    reading_count = len(valid_history)

    # -----------------------------------------------------
    # Not enough data
    # -----------------------------------------------------

    if reading_count < 2:
        return {
            "bin_id": str(bin_id),
            "prediction_available": False,
            "message": "Need at least 2 valid historical readings.",
            "current_fill_percent": (
                valid_history[-1]["fill_percent"]
                if valid_history
                else None
            ),
            "fill_rate_percent_per_hour": None,
            "predicted_fill_next_hour": None,
            "hours_to_90_percent": None,
            "overflow_risk": "UNKNOWN",
            "historical_readings": reading_count
        }

    # -----------------------------------------------------
    # Convert timestamps to elapsed hours
    # -----------------------------------------------------

    first_timestamp = valid_history[0]["timestamp"]

    x_values = []
    y_values = []

    for record in valid_history:
        elapsed_seconds = (
            record["timestamp"] - first_timestamp
        ).total_seconds()

        elapsed_hours = elapsed_seconds / 3600

        x_values.append(elapsed_hours)
        y_values.append(record["fill_percent"])

    # -----------------------------------------------------
    # Linear regression
    # -----------------------------------------------------

    slope, intercept = linear_regression(
        x_values,
        y_values
    )

    current_fill = y_values[-1]

    # -----------------------------------------------------
    # Handle identical timestamps
    # -----------------------------------------------------

    if slope is None:
        return {
            "bin_id": str(bin_id),
            "prediction_available": False,
            "message": (
                "Historical timestamps do not contain "
                "enough variation for regression."
            ),
            "current_fill_percent": round(current_fill, 2),
            "fill_rate_percent_per_hour": 0,
            "predicted_fill_next_hour": round(current_fill, 2),
            "hours_to_90_percent": (
                0 if current_fill >= 90 else None
            ),
            "overflow_risk": (
                "CRITICAL" if current_fill >= 90 else "UNKNOWN"
            ),
            "historical_readings": reading_count
        }

    # -----------------------------------------------------
    # Predict next-hour fill
    # -----------------------------------------------------

    current_time = x_values[-1]

    predicted_next_hour = (
        slope * (current_time + 1) + intercept
    )

    predicted_next_hour = max(
        0.0,
        min(100.0, predicted_next_hour)
    )

    # -----------------------------------------------------
    # Estimate time to 90% capacity
    # -----------------------------------------------------

    if current_fill >= 90:
        hours_to_90 = 0.0

    elif slope > 0:
        hours_to_90 = (90 - current_fill) / slope

    else:
        hours_to_90 = None

    # -----------------------------------------------------
    # Estimate overflow risk
    # -----------------------------------------------------

    if current_fill >= 90:
        risk = "CRITICAL"

    elif hours_to_90 is not None and hours_to_90 <= 2:
        risk = "HIGH"

    elif hours_to_90 is not None and hours_to_90 <= 6:
        risk = "MEDIUM"

    else:
        risk = "LOW"

    # -----------------------------------------------------
    # Return prediction
    # -----------------------------------------------------

    return {
        "bin_id": str(bin_id),
        "prediction_available": True,
        "current_fill_percent": round(current_fill, 2),
        "fill_rate_percent_per_hour": round(slope, 3),
        "predicted_fill_next_hour": round(
            predicted_next_hour, 2
        ),
        "hours_to_90_percent": (
            round(hours_to_90, 2)
            if hours_to_90 is not None
            else None
        ),
        "overflow_risk": risk,
        "historical_readings": reading_count
    }


# =========================================================
# CLOSE MONGODB CONNECTION
# =========================================================

def close_mongodb_connection():
    """
    Close the MongoDB client when the application shuts down.
    """

    client.close()

