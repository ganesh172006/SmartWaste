from prediction import predict_bin_fill


def calculate_ai_priority(bin_data, prediction):
    """
    Calculate collection priority using:
    - Current fill percentage
    - Fill growth rate
    - Predicted fill
    - Overflow risk
    """

    fill = float(
        bin_data.get("current_fill_percent", 0)
    )

    base_priority = float(
        bin_data.get("priority_score", 0)
    )

    # Handle unavailable predictions
    if not prediction.get("prediction_available", False):
        return {
            "ai_priority_score": base_priority,
            "ai_priority": bin_data.get("priority", "LOW"),
            "current_fill_percent": round(fill, 2),
            "growth_rate_percent_per_hour": 0,
            "predicted_fill_next_hour": fill,
            "hours_to_90_percent": None,
            "overflow_risk": "UNKNOWN",
            "reason": "Historical prediction unavailable"
        }

    growth_rate = float(
        prediction.get("fill_rate_percent_per_hour", 0)
    )

    predicted_fill = float(
        prediction.get("predicted_fill_next_hour", fill)
    )

    hours_to_90 = prediction.get(
        "hours_to_90_percent"
    )

    risk = prediction.get(
        "overflow_risk", "LOW"
    )

    # Start with the current fill percentage
    score = fill

    # Account for rapidly filling bins
    score += max(0, growth_rate) * 5

    # Predicted fill bonus
    if predicted_fill >= 100:
        score += 30
    elif predicted_fill >= 90:
        score += 25
    elif predicted_fill >= 80:
        score += 10

    # Time until 90% full
    if hours_to_90 is not None:
        if hours_to_90 <= 1:
            score += 30
        elif hours_to_90 <= 3:
            score += 20
        elif hours_to_90 <= 6:
            score += 10

    # Overflow risk bonus
    risk_bonus = {
        "CRITICAL": 40,
        "HIGH": 25,
        "MEDIUM": 10,
        "LOW": 0
    }

    score += risk_bonus.get(risk, 0)

    # Determine AI collection priority
    if risk == "CRITICAL":
        ai_priority = "IMMEDIATE"
    elif score >= 120:
        ai_priority = "URGENT"
    elif score >= 90:
        ai_priority = "HIGH"
    elif score >= 60:
        ai_priority = "MEDIUM"
    else:
        ai_priority = "LOW"

    return {
        "ai_priority_score": round(score, 2),
        "ai_priority": ai_priority,
        "current_fill_percent": round(fill, 2),
        "growth_rate_percent_per_hour": round(growth_rate, 3),
        "predicted_fill_next_hour": round(predicted_fill, 2),
        "hours_to_90_percent": hours_to_90,
        "overflow_risk": risk,
        "reason": f"Current fill {fill:.1f}%; risk {risk}"
    }


def generate_ai_route_candidates(bins):
    """
    Rank bins by AI collection priority.
    Coordinates are read from the nested location object.
    """

    candidates = []

    for bin_data in bins:
        bin_id = bin_data["bin_id"]

        location = bin_data.get("location", {})

        latitude = location.get("latitude")
        longitude = location.get("longitude")

        if latitude is None or longitude is None:
            print(
                f"Skipping {bin_id}: missing coordinates"
            )
            continue

        prediction = predict_bin_fill(bin_id)

        ai_result = calculate_ai_priority(
            bin_data,
            prediction
        )

        candidate = {
            "bin_id": bin_id,
            "location_name": location.get(
                "name", "Unknown location"
            ),
            "latitude": float(latitude),
            "longitude": float(longitude),
            "capacity_kg": bin_data.get(
                "capacity_kg", 100
            ),
            "current_fill_percent": bin_data.get(
                "current_fill_percent", 0
            ),
            **ai_result
        }

        candidates.append(candidate)

    # Highest priority first
    candidates.sort(
        key=lambda item: item["ai_priority_score"],
        reverse=True
    )

    return candidates