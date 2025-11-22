import pandas as pd
import orjson
import lz4.frame
import logging
from django.core.cache import cache
from datetime import timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

def _compress(obj):
    try:
        return lz4.frame.compress(orjson.dumps(obj, default=str))
    except Exception as e:
        logger.error(f"❌ Compression failed: {e}")
        raise

def _decompress(blob):
    try:
        return orjson.loads(lz4.frame.decompress(blob))
    except Exception as e:
        logger.error(f"❌ Decompression failed: {e}")
        return None

def cache_set(key, value, timeout=None):
    try:
        cache.set(key, _compress(value), timeout=timeout)
        logger.debug(f"✅ Cached key {key}")
    except Exception as e:
        logger.error(f"❌ Cache set failed for {key}: {e}")

def cache_get(key):
    blob = cache.get(key)
    if not blob:
        return None
    return _decompress(blob)

def chunk_and_cache_df(df, base_key, chunk_size=100000):
    try:
        cache.delete_pattern(f"{base_key}:chunk:*")

        for col in df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns:
            df[col] = df[col].astype(str)

        total_rows = len(df)
        if total_rows == 0:
            return

        num_chunks = (total_rows // chunk_size) + 1
        for i in range(num_chunks):
            chunk = df.iloc[i * chunk_size : (i + 1) * chunk_size]
            if not chunk.empty:
                cache_set(f"{base_key}:chunk:{i}", chunk.to_dict("records"))

        cache_set(f"{base_key}:chunk_count", num_chunks)
        logger.info(f"✅ Stored {num_chunks} chunks for key {base_key}")
    except Exception as e:
        logger.error(f"❌ Chunk and cache failed for {base_key}: {e}")

def read_all_chunks(base_key):
    """Read all DataFrame chunks back from Redis."""
    chunk_count = cache_get(f"{base_key}:chunk_count")
    if not chunk_count:
        return []
    all_data = []
    for i in range(chunk_count):
        part = cache_get(f"{base_key}:chunk:{i}")
        if part:
            all_data.extend(part)
    return all_data

def _safe_sum(series):
    """Safely sum a series even if it contains non-numeric data."""
    return float(series.sum()) if pd.api.types.is_numeric_dtype(series) else 0.0

def _make_summary(df):
    """Adaptive summary generator — only uses available columns."""
    summary = {"transactions": len(df)}
    if "total_fare" in df:
        summary["total_fare"] = _safe_sum(df["total_fare"])
    if "total_tkt_revenue" in df:
        summary["total_tkt_revenue"] = _safe_sum(df["total_tkt_revenue"])
    if "no_of_passengers" in df:
        summary["no_of_passengers"] = int(df["no_of_passengers"].sum())
    if "nrc_tkt_rev" in df:
        summary["nrc_tkt_rev"] = _safe_sum(df["nrc_tkt_rev"])
    if "gsd_tkt_rev" in df:
        summary["gsd_tkt_rev"] = _safe_sum(df["gsd_tkt_rev"])
    if "icrc_tkt_rev" in df:
        summary["icrc_tkt_rev"] = _safe_sum(df["icrc_tkt_rev"])
    return summary

def _compute_dimensions(df):
    """Adaptive grouped aggregates based on existing columns."""
    dims = {}
    if "coach_type_name" in df and "total_fare" in df:
        dims["by_coach"] = (
            df.groupby("coach_type_name")["total_fare"].sum().reset_index().to_dict("records")
        )
    if "booking_from" in df and "total_fare" in df:
        dims["by_station"] = (
            df.groupby("booking_from")["total_fare"].sum().reset_index().to_dict("records")
        )
    if "poc_corporation_name" in df and "total_fare" in df:
        dims["by_corporation"] = (
            df.groupby("poc_corporation_name")["total_fare"].sum().reset_index().to_dict("records")
        )
    if "user_name" in df and "total_fare" in df:
        dims["by_user"] = (
            df.groupby("user_name")["total_fare"].sum().reset_index().to_dict("records")
        )
    if "booking_date" in df and "total_fare" in df:
        daily = df.groupby("booking_date")["total_fare"].sum().reset_index()
        dims["daily_trend"] = daily.to_dict("records")
    return dims

def cache_aggregations(df, table_name="booking", date_col="booking_date"):

    if date_col not in df.columns:
        for fallback in ["created_at", "travel_date", "date", "booking_datetime"]:
            if fallback in df.columns:
                date_col = fallback
                break
        else:
            logger.warning(f"⚠️ No valid date column found in {table_name}, skipping aggregation.")
            return
        
    if df.empty:
        logger.warning(f"No data found for table {table_name} — skipping aggregation.")
        return

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.strftime("%Y-%m")
    df["week"] = df[date_col].dt.strftime("%Y-W%U")
    df["day"] = df[date_col].dt.strftime("%Y-%m-%d")

    for period, group_col in [("day", "day"), ("week", "week"), ("month", "month"), ("year", "year")]:
        for value, sub in df.groupby(group_col):
            key = f"{table_name}:agg:{period}:{value}"
            cache_set(key, {"summary": _make_summary(sub), **_compute_dimensions(sub)})

    logger.info(f"✅ Cached daily, weekly, monthly, yearly aggregations for {table_name}")

def _merge_group_list(rows, key_name):
    agg = defaultdict(float)
    for r in rows:
        agg[r[key_name]] += r["total_fare"]
    return [{key_name: k, "total_fare": v} for k, v in agg.items()]


def read_range(table_name, start_date, end_date):
    """Combine pre-aggregated data between two dates."""
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()
    cur = start
    keys = []
    while cur <= end:
        if cur.day == 1:
            month_end = (cur.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            if month_end <= end:
                keys.append(f"{table_name}:agg:month:{cur:%Y-%m}")
                cur = month_end + timedelta(days=1)
                continue
        week_start = cur - timedelta(days=cur.weekday())
        week_end = week_start + timedelta(days=6)
        iso_year, iso_week, _ = cur.isocalendar()
        if cur == week_start and week_end <= end:
            keys.append(f"{table_name}:agg:week:{iso_year}-W{iso_week:02d}")
            cur = week_end + timedelta(days=1)
            continue
        keys.append(f"{table_name}:agg:day:{cur:%Y-%m-%d}")
        cur += timedelta(days=1)

    total = defaultdict(float)
    by_coach_rows, by_station_rows, by_corp_rows, by_user_rows = [], [], [], []

    for k in keys:
        obj = cache_get(k) or {}
        s = obj.get("summary", {})
        for key, val in s.items():
            total[key] += val if isinstance(val, (int, float)) else 0
        by_coach_rows.extend(obj.get("by_coach", []))
        by_station_rows.extend(obj.get("by_station", []))
        by_corp_rows.extend(obj.get("by_corporation", []))
        by_user_rows.extend(obj.get("by_user", []))

    return {
        "summary": dict(total),
        "by_coach": _merge_group_list(by_coach_rows, "coach_type_name") if by_coach_rows else [],
        "by_station": _merge_group_list(by_station_rows, "booking_from") if by_station_rows else [],
        "by_corporation": _merge_group_list(by_corp_rows, "poc_corporation_name") if by_corp_rows else [],
        "by_user": _merge_group_list(by_user_rows, "user_name") if by_user_rows else [],
        "used_keys": keys
    }

def read_range_booking(start_date, end_date):
    return read_range("booking", start_date, end_date)

def read_range_validator(start_date, end_date):
    return read_range("validator", start_date, end_date)

def read_range_user(start_date, end_date):
    return read_range("user", start_date, end_date)

def safe_to_date(series):
    return pd.to_datetime(series, errors="coerce", format="mixed").dt.date

