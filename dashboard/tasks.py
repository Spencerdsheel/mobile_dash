from celery import shared_task
import pandas as pd
import logging
from .utils import chunk_and_cache_df, read_all_chunks, cache_aggregations
from .db import get_pg_connection, get_last_created_at_key, update_created_at_key

logger = logging.getLogger(__name__)

# ------------------ Booking Cache Update ------------------

@shared_task(bind=True)
def update_booking_cache(self):
    """Fetch new booking records and update Redis cache and aggregations."""
    try:
        logger.info("🔄 Updating booking cache...")
        conn = get_pg_connection()
        cursor = conn.cursor()

        base_key = "booking"
        last_created = get_last_created_at_key(base_key)

        cursor.execute("""
            SELECT id, booking_date, booking_from, booking_to,
                   coach_type_name, total_fare, total_tkt_revenue,
                   no_of_passengers, user_name, poc_corporation_name,
                   route_name, type, created_at
            FROM booking
            WHERE created_at > %s
            ORDER BY created_at ASC
        """, (last_created,))
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        if rows:
            new_df = pd.DataFrame(rows, columns=cols)
            old_data = read_all_chunks(base_key)
            old_df = pd.DataFrame(old_data) if old_data else pd.DataFrame()
            merged_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates(subset="id")

            chunk_and_cache_df(merged_df, base_key)
            cache_aggregations(merged_df, table_name=base_key, date_col="booking_date")
            update_created_at_key(base_key, new_df["created_at"].max())

            logger.info(f"✅ Booking cache updated with {len(new_df)} new rows.")
        else:
            logger.info("⚠️ No new booking data found.")

        cursor.close()
        conn.close()
    except Exception as e:
        logger.exception("🚨 Error in update_booking_cache:")
        raise self.retry(exc=e, countdown=60, max_retries=3)

# ------------------ Validator Cache Update ------------------

@shared_task(bind=True)
def update_validator_cache(self):
    """Fetch validator data and update Redis cache."""
    try:
        logger.info("🔄 Updating validator cache...")
        conn = get_pg_connection()
        cursor = conn.cursor()

        base_key = "validator"
        last_created = get_last_created_at_key(base_key)

        cursor.execute("""
            SELECT id, created_at, validator_name, passenger_name, ticket_id
            FROM validator
            WHERE created_at > %s
            ORDER BY created_at ASC
        """, (last_created,))
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        if rows:
            new_df = pd.DataFrame(rows, columns=cols)
            old_data = read_all_chunks(base_key)
            old_df = pd.DataFrame(old_data) if old_data else pd.DataFrame()
            merged_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates(subset="id")

            chunk_and_cache_df(merged_df, base_key)
            cache_aggregations(merged_df, table_name=base_key, date_col="created_at")
            update_created_at_key(base_key, new_df["created_at"].max())

            logger.info(f"✅ Validator cache updated with {len(new_df)} new rows.")
        else:
            logger.info("⚠️ No new validator data found.")

        cursor.close()
        conn.close()
    except Exception as e:
        logger.exception("🚨 Error in update_validator_cache:")
        raise self.retry(exc=e, countdown=60, max_retries=3)

# ------------------ User Cache Update ------------------

@shared_task(bind=True)
def update_user_cache(self):
    """Fetch user ticket data and update Redis cache."""
    try:
        logger.info("🔄 Updating user cache...")
        conn = get_pg_connection()
        cursor = conn.cursor()

        base_key = "user"
        last_created = get_last_created_at_key(base_key)

        cursor.execute("""
            SELECT id, user_name, total_fare, total_tkt_revenue,
                   nrc_tkt_rev, gsd_tkt_rev, icrc_tkt_rev,
                   no_of_passengers, booking_date, created_at
            FROM user_tickets
            WHERE created_at > %s
            ORDER BY created_at ASC
        """, (last_created,))
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        if rows:
            new_df = pd.DataFrame(rows, columns=cols)
            old_data = read_all_chunks(base_key)
            old_df = pd.DataFrame(old_data) if old_data else pd.DataFrame()
            merged_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates(subset="id")

            chunk_and_cache_df(merged_df, base_key)
            cache_aggregations(merged_df, table_name=base_key, date_col="booking_date")
            update_created_at_key(base_key, new_df["created_at"].max())

            logger.info(f"✅ User cache updated with {len(new_df)} new rows.")
        else:
            logger.info("⚠️ No new user data found.")

        cursor.close()
        conn.close()
    except Exception as e:
        logger.exception("🚨 Error in update_user_cache:")
        raise self.retry(exc=e, countdown=60, max_retries=3)
