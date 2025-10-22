import pandas as pd
import orjson
import lz4.frame
import logging
from django.core.cache import cache
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

# ------------------ Redis Compression ------------------

def _compress(obj):
    """Compress using ORJSON + LZ4 for performance."""
    return lz4.frame.compress(orjson.dumps(obj))

def _decompress(blob):
    """Decompress back to Python object."""
    return orjson.loads(lz4.frame.decompress(blob))

def cache_set(key, value, timeout=None):
    """Save compressed value in Redis cache."""
    try:
        cache.set(key, _compress(value), timeout=timeout)
        logger.debug(f"✅ Cached key {key}")
    except Exception as e:
        logger.error(f"❌ Cache set failed for {key}: {e}")

def cache_get(key):
    """Retrieve and decompress value from Redis cache."""
    blob = cache.get(key)
    if not blob:
        return None
    try:
        return _decompress(blob)
    except Exception as e:
        logger.error(f"❌ Cache get failed for {key}: {e}")
        return None

# ------------------ Chunked Data Storage ------------------

def chunk_and_cache_df(df, base_key, chunk_size=100000):
    """Store large DataFrame in Redis by chunking."""
    cache.delete_pattern(f"{base_key}:chunk:*")
    total_rows = len(df)
    if total_rows == 0:
        return
    num_chunks = (total_rows // chunk_size) + 1
    for i in range(num_chunks):
        start = i * chunk_size
        end = start + chunk_size
        chunk = df.iloc[start:end]
        if not chunk.empty:
            cache_set(f"{base_key}:chunk:{i}", chunk.to_dict("records"))
    cache_set(f"{base_key}:chunk_count", num_chunks)
    logger.info(f"✅ Stored {num_chunks} chunks for key {base_key}")

def read_all_chunks(base_key):
    """Read and merge all chunks from Redis."""
    chunk_count = cache_get(f"{base_key}:chunk_count")
    if not chunk_count:
        return []
    all_data = []
    for i in range(chunk_count):
        part = cache_get(f"{base_key}:chunk:{i}")
        if part:
            all_data.extend(part)
    return all_data

# ------------------ Aggregation Helpers ------------------

def _make_summary(df):
    """Generate key metrics summary."""
    return {
        "total_fare": float(df["total_fare"].sum()),
        "total_tkt_revenue": float(df.get("total_tkt_revenue", pd.Series()).sum()),
        "no_of_passengers": int(df.get("no_of_passengers", pd.Series()).sum()),
        "transactions": len(df)
    }

def _compute_dimensions(df):
    """Compute grouped dimensions for dashboard charts/tables."""
    dims = {}
    if "coach_type_name" in df:
        dims["by_coach"] = (
            df.groupby("coach_type_name")["total_fare"]
            .sum().reset_index().to_dict("records")
        )
    if "booking_from" in df:
        dims["by_station"] = (
            df.groupby("booking_from")["total_fare"]
            .sum().reset_index().to_dict("records")
        )
    if "poc_corporation_name" in df:
        dims["by_corporation"] = (
            df.groupby("poc_corporation_name")["total_fare"]
            .sum().reset_index().to_dict("records")
        )
    if "user_name" in df:
        dims["by_user"] = (
            df.groupby("user_name")["total_fare"]
            .sum().reset_index().to_dict("records")
        )
    if "booking_date" in df:
        daily = df.groupby("booking_date")["total_fare"].sum().reset_index()
        dims["daily_trend"] = daily.to_dict("records")
    return dims

# ------------------ Pre-Aggregation Logic ------------------

def cache_aggregations(df, table_name="booking", date_col="booking_date"):
    """
    Save daily, weekly, monthly, and yearly pre-aggregations to Redis.
    Each key stores summary + grouped data.
    """
    if df.empty:
        logger.warning(f"No data found for table {table_name} — skipping aggregation.")
        return

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.strftime("%Y-%m")
    df["week"] = df[date_col].dt.strftime("%Y-W%U")
    df["day"] = df[date_col].dt.strftime("%Y-%m-%d")

    for period, group_col in [
        ("day", "day"),
        ("week", "week"),
        ("month", "month"),
        ("year", "year")
    ]:
        for value, sub in df.groupby(group_col):
            key = f"{table_name}:agg:{period}:{value}"
            cache_set(key, {"summary": _make_summary(sub), **_compute_dimensions(sub)})
    logger.info(f"✅ Cached daily, weekly, monthly, yearly aggregations for {table_name}")

# ------------------ Range Reading (for Dash apps) ------------------

def _merge_group_list(rows, key_name):
    agg = defaultdict(float)
    for r in rows:
        agg[r[key_name]] += r["total_fare"]
    return [{key_name: k, "total_fare": v} for k, v in agg.items()]

def _read_range_generic(table_name, start_date, end_date):
    """Read and merge preaggregated Redis data for given date range."""
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()

    keys = []
    cur = start
    while cur <= end:
        # Try monthly key first
        if cur.day == 1:
            month_key = f"{table_name}:agg:month:{cur:%Y-%m}"
            if cache_get(month_key):
                keys.append(month_key)
                cur += timedelta(days=32)
                cur = cur.replace(day=1)
                continue
        # Try weekly key
        iso_year, iso_week, _ = cur.isocalendar()
        week_key = f"{table_name}:agg:week:{iso_year}-W{iso_week:02d}"
        if cache_get(week_key):
            keys.append(week_key)
            cur += timedelta(days=7)
            continue
        # Otherwise, use daily
        keys.append(f"{table_name}:agg:day:{cur:%Y-%m-%d}")
        cur += timedelta(days=1)

    summary_total = {"total_fare": 0, "total_tkt_revenue": 0, "no_of_passengers": 0, "transactions": 0}
    by_coach, by_station, by_corp, by_user = [], [], [], []

    for key in keys:
        obj = cache_get(key) or {}
        s = obj.get("summary", {})
        summary_total["total_fare"] += s.get("total_fare", 0)
        summary_total["total_tkt_revenue"] += s.get("total_tkt_revenue", 0)
        summary_total["no_of_passengers"] += s.get("no_of_passengers", 0)
        summary_total["transactions"] += s.get("transactions", 0)
        by_coach.extend(obj.get("by_coach", []))
        by_station.extend(obj.get("by_station", []))
        by_corp.extend(obj.get("by_corporation", []))
        by_user.extend(obj.get("by_user", []))

    return {
        "summary": summary_total,
        "by_coach": _merge_group_list(by_coach, "coach_type_name"),
        "by_station": _merge_group_list(by_station, "booking_from"),
        "by_corporation": _merge_group_list(by_corp, "poc_corporation_name"),
        "by_user": _merge_group_list(by_user, "user_name"),
        "used_keys": keys
    }

# Public functions for each table
def read_range_booking(start_date, end_date):
    return _read_range_generic("booking", start_date, end_date)

def read_range_validator(start_date, end_date):
    return _read_range_generic("validator", start_date, end_date)

def read_range_user(start_date, end_date):
    return _read_range_generic("user", start_date, end_date)
