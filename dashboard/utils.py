import os
import math
import logging
import pandas as pd
import psycopg2
from django.core.cache import cache

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# -------------------- Chunking Logic --------------------
def chunk_and_cache_df(df, key_prefix, chunk_size=10000):
    records = df.to_dict(orient='records')
    total_records = len(records)
    num_chunks = math.ceil(total_records / chunk_size)

    for i in range(num_chunks):
        chunk = records[i * chunk_size : (i + 1) * chunk_size]
        cache.set(f"{key_prefix}_chunk_{i}", chunk, timeout=None)

    cache.set(f"{key_prefix}_chunk_count", num_chunks, timeout=None)
    logger.debug(f"Stored {key_prefix} in {num_chunks} chunks.")

def read_all_chunks(key_prefix):
    chunks = []
    chunk_count = cache.get(f"{key_prefix}_chunk_count") or 0
    for i in range(chunk_count):
        chunk = cache.get(f"{key_prefix}_chunk_{i}")
        if chunk:
            chunks.extend(chunk)
    return chunks

def get_booking_data():
    return read_all_chunks("dashboard_data")

def get_validator_data():
    return read_all_chunks("validator_data")

def get_user_data():
    return read_all_chunks("user_data")

# -------------------- Main Function --------------------
def get_cached_dashboard_data():
    # Try reading from cache
    data = read_all_chunks("dashboard_data")
    if data:
        print("Fetched dashboard data from cache.")
        return data

    print("Cache is empty. Fetching data from DB...")

    try:
        # PostgreSQL Connection
        connection = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cursor = connection.cursor()

        # 1️⃣ Booking Table
        query = """
            SELECT id, booking_date, booking_from, booking_id, booking_to, coach_type_name, fultterwave_charge, gsd_cov_fee, 
            gsd_tkt_rev, icrc_tkt_rev, insurance, medical, nrc_cov_fee, nrc_tkt_rev, no_of_passengers, pnr_number, seat_type, 
            stamp_duty, booking_status, total_cov_fee, total_fare, total_tkt_revenue, train_name, travel_date, type, user_name,
            user_type, created_at, route_name, poc_corporation_name 
            FROM booking ORDER BY booking_date;
        """
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(cursor.fetchall(), columns=columns)
        chunk_and_cache_df(df, "dashboard_data")

        # 2️⃣ Validator Table
        validator_query = """
            SELECT id, status, booking_id, validated_at, created_at, updated_at 
            FROM booking_verification_details ORDER BY created_at;
        """
        cursor.execute(validator_query)
        validator_columns = [desc[0] for desc in cursor.description]
        validator_df = pd.DataFrame(cursor.fetchall(), columns=validator_columns)
        chunk_and_cache_df(validator_df, "validator_data")

        # 3️⃣ User Table
        user_query = """
            SELECT id, booking_id, coach_name, passenger_identification_number, passenger_contact, passenger_email, 
            passenger_name, passenger_type, seat_number, seat_type, created_at, updated_at 
            FROM booking_details ORDER BY created_at;
        """
        cursor.execute(user_query)
        user_columns = [desc[0] for desc in cursor.description]
        user_df = pd.DataFrame(cursor.fetchall(), columns=user_columns)
        chunk_and_cache_df(user_df, "user_data")

        cursor.close()
        connection.close()
        print("DB connection closed. All data cached in chunks.")

        # Return booking data for immediate use
        return df.to_dict(orient='records')

    except Exception as e:
        logger.error(f"DB Fetch Error: {e}")
        return "Failed to fetch data."
