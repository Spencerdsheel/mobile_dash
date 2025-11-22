import os
import psycopg2
import pandas as pd
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def get_pg_connection():
    
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        return conn
    except Exception as e:
        logger.error(f"🚨 PostgreSQL connection failed: {e}")
        raise


def get_last_created_at_key(base_key):
    """Retrieve the last cached 'created_at' timestamp for incremental updates."""
    try:
        val = cache.get(f"{base_key}:last_created_at")
        if val:
            return pd.Timestamp(val)
        return pd.Timestamp("2000-01-01")
    except Exception as e:
        logger.error(f"❌ Failed to get last created_at key for {base_key}: {e}")
        return pd.Timestamp("2000-01-01")

def update_created_at_key(base_key, timestamp):
    """Store the most recent 'created_at' timestamp in Redis."""
    try:
        if pd.notna(timestamp):
            cache.set(f"{base_key}:last_created_at", str(timestamp))
            logger.info(f"✅ Updated last_created_at key for {base_key}: {timestamp}")
    except Exception as e:
        logger.error(f"❌ Failed to update last_created_at key for {base_key}: {e}")
