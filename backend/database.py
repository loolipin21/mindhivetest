import psycopg2
from psycopg2.extras import RealDictCursor
import os

# PostgreSQL Connection Details
DB_CONFIG = {
    "dbname": "subway_db",
    "user": "subway_admin",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

# Function to Connect to PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    return conn
