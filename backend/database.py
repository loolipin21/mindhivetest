import psycopg2
from psycopg2.extras import RealDictCursor

# PostgreSQL Connection Details for Neon
DB_CONFIG = {
    "dbname": "neondb",  # Update with your actual Neon database name
    "user": "neondb_owner",  # Your Neon database username
    "password": "npg_Jka8NAQDojI1",  # Your Neon password
    "host": "ep-broad-cake-a18sjkj4-pooler.ap-southeast-1.aws.neon.tech",  # Your Neon host
    "port": "5432",  # PostgreSQL default port
    "sslmode": "require"  # Required for Neon connections
}

# Function to Connect to PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    return conn


import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "sslmode": "require"
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        print("✅ Database connection successful!")  # Debug log
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")  # Error log
        return None
