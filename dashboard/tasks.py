# tasks.py

import os
import pandas as pd
from celery import shared_task
from datetime import datetime
import psycopg2
from django.core.cache import cache
from .utils import (
    chunk_and_cache_df, read_all_chunks,
    cache_booking_aggregations, cache_validator_aggregations, cache_user_aggregations
)

import logging
logger = logging.getLogger(__name__)

# -------------------- DB Connection --------------------
def get_pg_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

# -------------------- Cache timestamp helpers --------------------
def get_last_created_at_key(key_prefix):
    records = read_all_chunks(key_prefix)
    if not records:
        return datetime(2023, 1, 1, 0, 0, 0)

    df = pd.DataFrame(records)
    if "created_at" in df.columns and not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        if df["created_at"].notnull().any():
            return df["created_at"].max()

    return datetime(2023, 1, 1, 0, 0, 0)

def update_created_at_key(key_prefix, latest_timestamp):
    cache.set(f"{key_prefix}:latest_ts", latest_timestamp.strftime("%Y-%m-%d %H:%M:%S"))

# -------------------- Celery Task --------------------
@shared_task(bind=True)
def update_dashboard_data(self):
    try:
        logger.info("🔄 Starting dashboard data update task.")
        conn = get_pg_connection()
        cursor = conn.cursor()

        # ===== Booking Table =====
        booking_key = "dashboard_data"
        last_booking_created = get_last_created_at_key(booking_key)
        cursor.execute("""
            SELECT id, booking_date, booking_from, booking_id, booking_to, coach_type_name,
                   gsd_tkt_rev, icrc_tkt_rev, insurance, medical, nrc_tkt_rev,
                   no_of_passengers, total_fare, total_tkt_revenue,
                   user_name, user_type, created_at, poc_corporation_name
            FROM booking
            WHERE created_at > %s
            ORDER BY created_at ASC
        """, (last_booking_created,))
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        if rows:
            new_df = pd.DataFrame(rows, columns=cols)
            old_records = read_all_chunks(booking_key)
            old_df = pd.DataFrame(old_records) if old_records else pd.DataFrame()
            merged_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates(subset="id")

            chunk_and_cache_df(merged_df, booking_key)
            update_created_at_key(booking_key, new_df["created_at"].max())
            cache_booking_aggregations(merged_df, date_col="booking_date")
            logger.info(f"✅ Cached {len(new_df)} booking rows with aggregations.")
        else:
            logger.info("⚠️ No new booking data.")

        # ===== Validator Table =====
        validator_key = "validator_data"
        last_validator_created = get_last_created_at_key(validator_key)
        cursor.execute("""
            SELECT id, status, booking_id, validated_at, created_at
            FROM booking_verification_details
            WHERE created_at > %s
            ORDER BY created_at ASC
        """, (last_validator_created,))
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        if rows:
            new_df = pd.DataFrame(rows, columns=cols)
            old_records = read_all_chunks(validator_key)
            old_df = pd.DataFrame(old_records) if old_records else pd.DataFrame()
            merged_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates(subset="id")

            chunk_and_cache_df(merged_df, validator_key)
            update_created_at_key(validator_key, new_df["created_at"].max())
            cache_validator_aggregations(merged_df, date_col="created_at")
            logger.info(f"✅ Cached {len(new_df)} validator rows with aggregations.")
        else:
            logger.info("⚠️ No new validator data.")

        # ===== User Table =====
        user_key = "user_data"
        last_user_created = get_last_created_at_key(user_key)
        cursor.execute("""
            SELECT id, booking_id, passenger_identification_number, passenger_contact,
                   passenger_email, passenger_name, passenger_type,
                   seat_number, seat_type, created_at
            FROM booking_details
            WHERE created_at > %s
            ORDER BY created_at ASC
        """, (last_user_created,))
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        if rows:
            new_df = pd.DataFrame(rows, columns=cols)
            old_records = read_all_chunks(user_key)
            old_df = pd.DataFrame(old_records) if old_records else pd.DataFrame()
            merged_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates(subset="id")

            chunk_and_cache_df(merged_df, user_key)
            update_created_at_key(user_key, new_df["created_at"].max())
            cache_user_aggregations(merged_df, date_col="created_at")
            logger.info(f"✅ Cached {len(new_df)} user rows with aggregations.")
        else:
            logger.info("⚠️ No new user data.")

        cursor.close()
        conn.close()
        logger.info("🎉 Dashboard task finished successfully.")
        return "All 3 tables processed and cached successfully."

    except Exception as e:
        logger.exception("🚨 Error in update_dashboard_data task:")
        raise self.retry(exc=e, countdown=60, max_retries=3)
