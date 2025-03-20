import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "sslmode": "prefer"
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        print("✅ Database connection successful!")  
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}") 
        return None

# For Local db testing
# import psycopg2
# from psycopg2.extras import RealDictCursor
# import os

# # PostgreSQL Connection Details
# DB_CONFIG = {
#     "dbname": "subway_db",
#     "user": "subway_admin",
#     "password": "password",
#     "host": "localhost",
#     "port": "5432"
# }

# # Function to Connect to PostgreSQL
# def get_db_connection():
#     conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
#     return conn
