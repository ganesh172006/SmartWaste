from pymongo import MongoClient

from ai_route_optimizer import (
    generate_ai_route_candidates
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

results = generate_ai_route_candidates(
    bins
)

print()
print(
    "======================================"
)

print(
    "AI SMART COLLECTION PRIORITY"
)

print(
    "======================================"
)

for item in results:

    print(
        f"""
{item['bin_id']}
Current Fill : {item['current_fill_percent']}%
Growth Rate  : {item['growth_rate_percent_per_hour']}%/hr
Next Hour    : {item['predicted_fill_next_hour']}%
Risk         : {item['overflow_risk']}
AI Score     : {item['ai_priority_score']}
AI Priority  : {item['ai_priority']}
"""
    )