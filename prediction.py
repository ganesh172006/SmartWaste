from datetime import datetime
from pymongo import MongoClient


# =========================================================
# MONGODB CONNECTION
# =========================================================

MONGO_URL = "mongodb://localhost:27017/"

client = MongoClient(MONGO_URL)

db = client["smart_waste"]

history_collection = db["bin_history"]


# =========================================================
# SAVE BIN HISTORY
# =========================================================

def save_bin_history(bin_id, fill_percent):

    history_collection.insert_one({

        "bin_id": bin_id,

        "fill_percent": float(fill_percent),

        "timestamp": datetime.now()

    })


# =========================================================
# GET BIN HISTORY
# =========================================================

def get_bin_history(bin_id):

    history = list(

        history_collection.find(

            {
                "bin_id": bin_id
            },

            {
                "_id": 0
            }

        ).sort(

            "timestamp",
            1

        )

    )

    return history


# =========================================================
# LINEAR REGRESSION
# =========================================================

def linear_regression(
    x_values,
    y_values
):

    n = len(x_values)

    if n < 2:

        return None, None


    x_mean = (
        sum(x_values) / n
    )

    y_mean = (
        sum(y_values) / n
    )


    numerator = sum(

        (x - x_mean)
        *
        (y - y_mean)

        for x, y
        in zip(
            x_values,
            y_values
        )

    )


    denominator = sum(

        (x - x_mean) ** 2

        for x
        in x_values

    )


    if denominator == 0:

        return None, None


    slope = (
        numerator /
        denominator
    )


    intercept = (
        y_mean -
        slope * x_mean
    )


    return (
        slope,
        intercept
    )


# =========================================================
# PREDICT BIN FILL
# =========================================================

def predict_bin_fill(bin_id):

    # ---------------------------------------------
    # Get historical records
    # ---------------------------------------------

    history = get_bin_history(
        bin_id
    )


    # ---------------------------------------------
    # Not enough data
    # ---------------------------------------------

    if len(history) < 2:

        return {

            "bin_id": bin_id,

            "prediction_available": False,

            "message":
                "Need at least 2 historical readings.",

            "current_fill_percent":
                None,

            "fill_rate_percent_per_hour":
                None,

            "predicted_fill_next_hour":
                None,

            "hours_to_90_percent":
                None,

            "overflow_risk":
                "UNKNOWN",

            "historical_readings":
                len(history)

        }


    # ---------------------------------------------
    # First timestamp
    # ---------------------------------------------

    first_timestamp = history[0][
        "timestamp"
    ]


    x_values = []

    y_values = []


    # ---------------------------------------------
    # Convert timestamps to hours
    # ---------------------------------------------

    for record in history:

        timestamp = record[
            "timestamp"
        ]


        elapsed_seconds = (

            timestamp -
            first_timestamp

        ).total_seconds()


        elapsed_hours = (

            elapsed_seconds /
            3600

        )


        x_values.append(
            elapsed_hours
        )


        y_values.append(

            float(
                record[
                    "fill_percent"
                ]
            )

        )


    # ---------------------------------------------
    # Linear regression
    # ---------------------------------------------

    slope, intercept = linear_regression(

        x_values,

        y_values

    )


    if slope is None:

        return {

            "bin_id": bin_id,

            "prediction_available": False,

            "message":
                "Historical values do not contain enough variation.",

            "current_fill_percent":
                y_values[-1],

            "fill_rate_percent_per_hour":
                0,

            "predicted_fill_next_hour":
                y_values[-1],

            "hours_to_90_percent":
                None,

            "overflow_risk":
                "UNKNOWN",

            "historical_readings":
                len(history)

        }


    # ---------------------------------------------
    # Current fill
    # ---------------------------------------------

    current_fill = y_values[-1]

    current_time = x_values[-1]


    # ---------------------------------------------
    # Predict next hour
    # ---------------------------------------------

    predicted_next_hour = (

        slope *
        (current_time + 1)

        +

        intercept

    )


    # Keep between 0 and 100

    predicted_next_hour = max(

        0,

        min(
            100,
            predicted_next_hour
        )

    )


    # ---------------------------------------------
    # Calculate time to 90%
    # ---------------------------------------------

    if current_fill >= 90:

        hours_to_90 = 0


    elif slope > 0:

        hours_to_90 = (

            (90 - current_fill)
            /
            slope

        )


        if hours_to_90 < 0:

            hours_to_90 = 0


    else:

        hours_to_90 = None


    # ---------------------------------------------
    # Calculate risk
    # ---------------------------------------------

    if current_fill >= 90:

        risk = "CRITICAL"


    elif (

        hours_to_90 is not None

        and

        hours_to_90 <= 2

    ):

        risk = "HIGH"


    elif (

        hours_to_90 is not None

        and

        hours_to_90 <= 6

    ):

        risk = "MEDIUM"


    else:

        risk = "LOW"


    # ---------------------------------------------
    # Return prediction
    # ---------------------------------------------

    return {

        "bin_id":
            bin_id,

        "prediction_available":
            True,

        "current_fill_percent":
            round(
                current_fill,
                2
            ),

        "fill_rate_percent_per_hour":
            round(
                slope,
                3
            ),

        "predicted_fill_next_hour":
            round(
                predicted_next_hour,
                2
            ),

        "hours_to_90_percent":

            round(
                hours_to_90,
                2
            )

            if hours_to_90 is not None

            else None,

        "overflow_risk":
            risk,

        "historical_readings":
            len(history)

    }