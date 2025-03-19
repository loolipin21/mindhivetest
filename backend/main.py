from fastapi import FastAPI, Query
from database import get_db_connection
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI()

# ✅ Allow CORS (Frontend can access Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change "*" to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Endpoint: Fetch All Subway Outlets
@app.get("/outlets/")
def get_outlets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subway_outlets;")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# ✅ Endpoint: Search by Name
@app.get("/outlets/search/")
def search_outlets(name: str = Query(..., description="Search for a Subway outlet by name")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subway_outlets WHERE name ILIKE %s;", (f"%{name}%",))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# ✅ Endpoint: Search by Location (Latitude & Longitude)
@app.get("/outlets/nearby/")
def search_nearby(lat: float, lon: float, radius: float = 0.05):
    query = """
    SELECT *, 
    (ABS(latitude::FLOAT - %s) + ABS(longitude::FLOAT - %s)) AS distance
    FROM subway_outlets
    WHERE (ABS(latitude::FLOAT - %s) + ABS(longitude::FLOAT - %s)) <= %s
    ORDER BY distance ASC;
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, (lat, lon, lat, lon, radius))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# ✅ Endpoint: Search by City (Filter by Address)
@app.get("/outlets/city/")
def search_by_city(city: str = Query(..., description="Filter Subway outlets by city")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subway_outlets WHERE address ILIKE %s;", (f"%{city}%",))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# ✅ Root URL
@app.get("/")
def home():
    return {"message": "Welcome to the Subway Outlets API 🚀"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Use Railway-assigned port
    print(f"🚀 Starting FastAPI on port {port}...")  # Log output
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")