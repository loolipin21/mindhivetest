from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import psycopg2
import time

# PostgreSQL Connection Details
DB_CONFIG = {
    "dbname": "subway_db",
    "user": "subway_admin",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

# Initialize Selenium WebDriver
options = webdriver.ChromeOptions()
# Disable headless mode for debugging
# options.add_argument("--headless")  

# Simulate human-like behavior
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://subway.com.my/find-a-subway")

# Wait for the search box
wait = WebDriverWait(driver, 20)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

# Locate search box and input "Kuala Lumpur"
try:
    search_box = wait.until(EC.presence_of_element_located((By.ID, "fp_searchAddress")))
    search_box.send_keys("Kuala Lumpur")
    search_box.send_keys(Keys.RETURN)
    print("Search successful!")
except Exception as e:
    print("Error locating search box:", e)
    driver.quit()
    exit()

# Allow extra time for JavaScript to load
time.sleep(10)

# Wait for outlet list
try:
    wait.until(EC.presence_of_element_located((By.ID, "fp_locationlist")))
    print("Outlet list loaded successfully.")
except:
    print("Outlet list not found! Exiting script.")
    driver.quit()
    exit()

# Scroll multiple times to force load dynamic content
for _ in range(3):  
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

# Extract outlets using the correct class `fp_listitem`
outlets = driver.find_elements(By.CLASS_NAME, "fp_listitem")

# **Debugging: Print outlet count**
print(f"Found {len(outlets)} outlets (before filtering by display: flex).")

outlet_data = []

for outlet in outlets:
    try:
        # **Fix: Ensure only elements with `display: flex` are considered**
        style_attribute = outlet.get_attribute("style")
        if "display: none" in style_attribute:
            print("Skipping hidden outlet (display: none)")
            continue  # Skip elements that are hidden

        # Extract latitude & longitude
        latitude = outlet.get_attribute("data-latitude")
        longitude = outlet.get_attribute("data-longitude")

        # Extract name (inside .location_left > h4)
        name_element = outlet.find_element(By.CLASS_NAME, "location_left").find_element(By.TAG_NAME, "h4")
        name = name_element.text.strip() if name_element else "No Name"

        # Extract address and operating hours dynamically
        address_element = outlet.find_element(By.CLASS_NAME, "infoboxcontent")
        address_lines = address_element.find_elements(By.TAG_NAME, "p")

        # **Fix: First `<p>` is always the address**
        address = address_lines[0].text.strip() if len(address_lines) > 0 else "No Address"

        # **Fix: Detect all `<p>` lines and format operating hours properly**
        operating_hours = []
        for p in address_lines[1:]:  # Ignore first `<p>` (Address)
            text = p.text.strip()
            if ":" in text or "AM" in text or "PM" in text or "Closed" in text:  # Detect time format
                operating_hours.append(text)

        # Format operating hours as a single string
        formatted_hours = "; ".join(operating_hours) if operating_hours else "No Operating Hours"

        # Extract Waze Link (inside .location_right > .directionButton > a)
        try:
            waze_link_element = outlet.find_element(By.CLASS_NAME, "location_right").find_element(By.CLASS_NAME, "directionButton").find_elements(By.TAG_NAME, "a")
            waze_link = waze_link_element[1].get_attribute("href") if len(waze_link_element) > 1 else None
        except:
            waze_link = None

        # **Fix: Skip empty rows**
        if name == "No Name" or address == "No Address":
            print(f"Skipping empty entry: {name}, {address}")
            continue  # Skip inserting blank rows

        # Debugging: Print extracted data
        print(f"Extracted: {name}, {address}, {formatted_hours}, {latitude}, {longitude}, {waze_link}")

        outlet_data.append((name, address, formatted_hours, latitude, longitude, waze_link))

    except Exception as e:
        print(f"Skipping an entry due to error: {e}")

# Close Selenium
driver.quit()

# Store data in PostgreSQL
def insert_data(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subway_outlets (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            operating_hours TEXT,
            latitude TEXT,
            longitude TEXT,
            waze_link TEXT
        )
    """)

    for entry in data:
        cursor.execute("""
            INSERT INTO subway_outlets (name, address, operating_hours, latitude, longitude, waze_link) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, entry)

    conn.commit()
    cursor.close()
    conn.close()

# Insert the scraped data
if outlet_data:
    insert_data(outlet_data)
    print(f"Stored {len(outlet_data)} Subway outlets in PostgreSQL!")
else:
    print("No outlets found! Check if JavaScript is blocking content.")
