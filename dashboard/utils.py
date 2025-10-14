# utils.py

import os
import math
import logging
import pandas as pd
import orjson
import lz4.frame
from django.core.cache import cache
from datetime import timedelta
from collections import defaultdict

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# -------------------- Chunking Logic --------------------
def chunk_and_cache_df(df, key_prefix, chunk_size=10000):
    """Save DataFrame in Redis chunks with compression."""
    for col in df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]):
        df[col] = df[col].astype(str)

    records = df.to_dict(orient="records")
    total_records = len(records)
    num_chunks = math.ceil(total_records / chunk_size)

    for i in range(num_chunks):
        chunk = records[i * chunk_size : (i + 1) * chunk_size]
        try:
            compressed = lz4.frame.compress(orjson.dumps(chunk))
            cache.set(f"{key_prefix}_chunk_{i}", compressed, timeout=None)
        except Exception as e:
            logger.error(f"❌ Failed to save {key_prefix}_chunk_{i}: {e}")

    cache.set(f"{key_prefix}_chunk_count", num_chunks, timeout=None)
    logger.info(f"✅ Stored {total_records} rows for {key_prefix} in {num_chunks} chunks.")

def read_all_chunks(key_prefix):
    """Read all chunks for a given prefix from Redis."""
    chunks = []
    chunk_count = cache.get(f"{key_prefix}_chunk_count")
    if isinstance(chunk_count, bytes):
        chunk_count = int(chunk_count.decode())
    chunk_count = chunk_count or 0

    for i in range(chunk_count):
        compressed = cache.get(f"{key_prefix}_chunk_{i}")
        if compressed:
            try:
                chunk = orjson.loads(lz4.frame.decompress(compressed))
                chunks.extend(chunk)
            except Exception as e:
                logger.error(f"❌ Failed to load {key_prefix}_chunk_{i}: {e}")
        else:
            logger.warning(f"⚠️ Missing {key_prefix}_chunk_{i}")
    return chunks

# -------------------- Aggregation Helpers --------------------
def _merge_group_list(rows, key_name):
    agg = defaultdict(float)
    for r in rows:
        agg[r[key_name]] += r["value"]
    return [{key_name: k, "value": v} for k, v in agg.items()]

def _make_summary(df, value_col="total_fare", count_col="id"):
    return {
        "total_value": float(df[value_col].sum()) if value_col in df else 0.0,
        "count": int(df[count_col].count()) if count_col in df else 0,
    }

# -------------------- Booking Aggregations --------------------
def cache_booking_aggregations(df, date_col="booking_date"):
    """Cache booking data aggregations by day/week/month/year."""
    if df.empty: return
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.strftime("%Y-%m")
    df["week"] = df[date_col].dt.strftime("%Y-W%U")
    df["day"] = df[date_col].dt.strftime("%Y-%m-%d")

    def _compute_dimensions(sub):
        dims = {}
        if "coach_type_name" in sub:
            dims["by_coach"] = sub.groupby("coach_type_name")["total_fare"].sum().reset_index().to_dict("records")
        if "booking_from" in sub:
            dims["by_station"] = sub.groupby("booking_from")["total_fare"].sum().reset_index().to_dict("records")
        if "poc_corporation_name" in sub:
            dims["by_corporation"] = sub.groupby("poc_corporation_name")["total_fare"].sum().reset_index().to_dict("records")
        if "user_name" in sub:
            dims["by_user"] = sub.groupby("user_name")["total_fare"].sum().reset_index().to_dict("records")
        if "booking_date" in sub:
            daily = sub.groupby("booking_date")["total_fare"].sum().reset_index()
            dims["daily_trend"] = daily.to_dict("records")
        return dims

    for level, col in [("day", "day"), ("week", "week"), ("month", "month"), ("year", "year")]:
        for key, sub in df.groupby(col):
            cache.set(
                f"dashboard:agg:booking:{level}:{key}",
                {"summary": _make_summary(sub, "total_fare", "id"), **_compute_dimensions(sub)},
                timeout=None,
            )

# -------------------- Validator Aggregations --------------------
def cache_validator_aggregations(df, date_col="created_at"):
    """Cache validator data aggregations."""
    if df.empty: return
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.strftime("%Y-%m")
    df["week"] = df[date_col].dt.strftime("%Y-W%U")
    df["day"] = df[date_col].dt.strftime("%Y-%m-%d")

    def _compute_dimensions(sub):
        dims = {}
        if "status" in sub:
            dims["by_status"] = sub.groupby("status")["id"].count().reset_index().rename(columns={"id": "count"}).to_dict("records")
        return dims

    for level, col in [("day", "day"), ("week", "week"), ("month", "month"), ("year", "year")]:
        for key, sub in df.groupby(col):
            cache.set(
                f"dashboard:agg:validator:{level}:{key}",
                {"summary": _make_summary(sub, "id", "id"), **_compute_dimensions(sub)},
                timeout=None,
            )

# -------------------- User Aggregations --------------------
def cache_user_aggregations(df, date_col="created_at"):
    """Cache user/passenger data aggregations."""
    if df.empty: return
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.strftime("%Y-%m")
    df["week"] = df[date_col].dt.strftime("%Y-W%U")
    df["day"] = df[date_col].dt.strftime("%Y-%m-%d")

    def _compute_dimensions(sub):
        dims = {}
        if "passenger_type" in sub:
            dims["by_passenger_type"] = sub.groupby("passenger_type")["id"].count().reset_index().rename(columns={"id": "count"}).to_dict("records")
        return dims

    for level, col in [("day", "day"), ("week", "week"), ("month", "month"), ("year", "year")]:
        for key, sub in df.groupby(col):
            cache.set(
                f"dashboard:agg:user:{level}:{key}",
                {"summary": _make_summary(sub, "id", "id"), **_compute_dimensions(sub)},
                timeout=None,
            )
