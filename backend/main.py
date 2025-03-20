from fastapi import FastAPI, Query
from database import get_db_connection
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import os
import spacy
import re
from datetime import datetime
from fastapi.responses import JSONResponse


# Initialize FastAPI
app = FastAPI()
nlp = spacy.load("en_core_web_sm")

@app.on_event("startup")
async def startup_event():
    if not hasattr(app.state, "pending_selections"):
        app.state.pending_selections = {}

def fetch_all_locations():
    """Retrieve all locations dynamically from the database, including names, addresses, and coordinates."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, address, latitude, longitude FROM subway_outlets;")
    results = cursor.fetchall()

    locations = {row["address"]: {
        "name": row["name"],
        "address": row["address"],
        "latitude": row["latitude"],
        "longitude": row["longitude"]
    } for row in results}

    cursor.close()
    conn.close()
    return locations 


import logging
logging.basicConfig(level=logging.INFO)

def fetch_closing_time(location: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, operating_hours FROM subway_outlets WHERE address ILIKE %s;", (f"%{location}%",))
    result = cursor.fetchone()
    if result:
        outlet_name = result['name']
        raw_hours = result['operating_hours']
        cursor.close()
        conn.close()
        
        return JSONResponse(content={
            "status": "success",
            "outlet": outlet_name,
            "location": location,
            "operating_hours": raw_hours,  
        })

    cursor.close()
    conn.close()
    return JSONResponse(content={"status": "error", "message": f"No operating hours found for {location}."})

# ✅ Text Preprocessing Function (Regex & Lowercasing)
def preprocess_text(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Remove punctuation
    text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
    return text

# ✅ Enhanced NLP Processing Function
def process_query(query: str, all_locations: list, user_id: str):
    print(f"\n🔍 Processing Query: {query}")  
    query_lower = preprocess_text(query)
    matching_locations = []
    
    is_opening_query = any(word in query_lower for word in ["open", "opening", "start"])
    is_closing_query = any(word in query_lower for word in ["close", "closing", "end"])
    is_count_query = any(word in query_lower for word in ["how many", "count", "number", "total"])
    is_list_query = any(word in query_lower for word in ["list", "show all", "which outlets", "available outlets", "where"])
    query_location = None
    match = re.search(r"in (.+)$", query_lower)  # Looks for "in <location>"
    if match:
        query_location = match.group(1).strip() 
    for location in all_locations:
        location_lower = location.lower()
        query_words = [word for word in query_lower.split() if word not in ["the", "at", "in", "does", "what", "time", "hours"]]
        if any(word in location_lower for word in query_words):
            matching_locations.append(location)

    print(f"📌 Matched Locations: {matching_locations}")

    # ✅ Handle Count Queries
    if is_count_query:
        if matching_locations:
            return JSONResponse(content={
                "status": "success",
                "message": f"📍 There are {len(matching_locations)} Subway outlets in {query_location}."
            })
        else:
            return JSONResponse(content={"status": "error", "message": f"No Subway outlets found in {query_location}."})

    # ✅ Handle List Queries
    if is_list_query:
        if matching_locations:
            return JSONResponse(content={
                "status": "success",
                "message": f"📍 Subway outlets in the specified location:\n" + "\n".join(matching_locations)
            })
        else:
            return JSONResponse(content={"status": "error", "message": "No Subway outlets found in the location specified."})

    # ✅ Handle Opening/Closing Time Queries
    if len(matching_locations) == 1:
        return fetch_closing_time(matching_locations[0], is_opening_query, is_closing_query)

    elif len(matching_locations) > 1:
        if not hasattr(app.state, "pending_selections"):
            app.state.pending_selections = {}

        app.state.pending_selections[user_id] = matching_locations

        options_list = "\n".join([f"{i+1}. {loc}" for i, loc in enumerate(matching_locations)])

        return JSONResponse(content={
            "status": "multiple",
            "message": f"Multiple Subway locations found. Please select one from the list:",
            "options": matching_locations  
        })

    else:
        return JSONResponse(content={"status": "error", "message": "I couldn't find a Subway in the location you mentioned."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/outlets/nearest/")
def search_nearest(lat: float = Query(..., description="User latitude"), lon: float = Query(..., description="User longitude"), radius: float = 5.0):
    """
    Find the nearest Subway outlets within the specified radius (default 5KM).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT name, address, latitude, longitude, 
           (ABS(latitude::FLOAT - %s) + ABS(longitude::FLOAT - %s)) AS distance
    FROM subway_outlets
    WHERE (ABS(latitude::FLOAT - %s) + ABS(longitude::FLOAT - %s)) <= %s
    ORDER BY distance ASC
    LIMIT 5;
    """
    cursor.execute(query, (lat, lon, lat, lon, radius))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if results:
        response = "\n".join([f"{res['name']} 📍 {res['address']}" for res in results])
        return JSONResponse(content={
            "status": "success",
            "message": f"🔍 Nearest Subway outlets:\n{response}"
        })
    else:
        return JSONResponse(content={"status": "error", "message": "No Subway outlets found nearby."})


@app.get("/select/")
def select_location(user_id: str = Query(...), choice: int = Query(...)):
    # Read from app.state.pending_selections
    if (
        not hasattr(app.state, "pending_selections")
        or user_id not in app.state.pending_selections
    ):
        return JSONResponse(content={"status": "error", "message": "No pending selection found."})

    locations = app.state.pending_selections[user_id]
    
    if choice < 1 or choice > len(locations):
        return JSONResponse(content={"status": "error", "message": "Invalid selection. Please choose a valid number."})

    selected_location = locations[choice - 1]
    del app.state.pending_selections[user_id]  
    print("SELECTED LOCATION")
    print(select_location)
    return fetch_closing_time(selected_location)


@app.get("/search/")
def search_chatbot(
    query: str = Query(..., description="Ask about Subway outlet details"), 
    user_id: str = Query(...)
):
    all_locations = fetch_all_locations()
    response = process_query(query, all_locations, user_id)
    return response

@app.get("/outlets/")
def get_outlets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subway_outlets;")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

@app.get("/outlets/search/")
def search_outlets(name: str = Query(..., description="Search for a Subway outlet by name")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subway_outlets WHERE name ILIKE %s;", (f"%{name}%",))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

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
