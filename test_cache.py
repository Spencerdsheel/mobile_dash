# test_cache.py
import pandas as pd
from utils import (
    chunk_and_cache_df, read_all_chunks,
    cache_booking_aggregations, cache_validator_aggregations, cache_user_aggregations
)
from django.core.cache import cache

# ---- Step 1: Dummy data ----
booking_df = pd.DataFrame([
    {"id": 1, "booking_date": "2025-09-01", "coach_type_name": "First Class",
     "booking_from": "Station A", "poc_corporation_name": "Corp1",
     "user_name": "Alice", "total_fare": 500, "total_tkt_revenue": 450,
     "no_of_passengers": 3, "created_at": "2025-09-01 12:00:00"},
    {"id": 2, "booking_date": "2025-09-02", "coach_type_name": "Standard Class",
     "booking_from": "Station B", "poc_corporation_name": "Corp2",
     "user_name": "Bob", "total_fare": 300, "total_tkt_revenue": 270,
     "no_of_passengers": 2, "created_at": "2025-09-02 15:00:00"}
])

validator_df = pd.DataFrame([
    {"id": 1, "booking_id": 1, "status": "SUCCESS", "created_at": "2025-09-01 13:00:00"},
    {"id": 2, "booking_id": 2, "status": "FAILED", "created_at": "2025-09-02 14:00:00"}
])

user_df = pd.DataFrame([
    {"id": 1, "booking_id": 1, "passenger_type": "Adult", "created_at": "2025-09-01 12:00:00"},
    {"id": 2, "booking_id": 2, "passenger_type": "Child", "created_at": "2025-09-02 15:00:00"}
])

# ---- Step 2: Test raw chunking ----
chunk_and_cache_df(booking_df, "dashboard_data")
print("Raw booking chunks:", read_all_chunks("dashboard_data"))

# ---- Step 3: Test pre-aggregations ----
cache_booking_aggregations(booking_df)
cache_validator_aggregations(validator_df)
cache_user_aggregations(user_df)

# ---- Step 4: Check Redis keys ----
import redis
r = redis.Redis(host="localhost", port=6379, db=0)

print("\n🔑 Keys in Redis:")
for k in r.keys("dashboard:agg:*"):
    print(k.decode(), "=>", r.get(k)[:200], "...")  # print first 200 bytes
