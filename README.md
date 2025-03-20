Subway Outlets API

This is a FastAPI-based backend application for querying Subway outlet locations, retrieving their operating hours, and performing geolocation-based searches. It is integrated with a PostgreSQL database and serves as a backend for a React-based frontend.

🚀 Features

Search Subway Outlets by name, location, or nearby radius

Retrieve operating hours for specific outlets

List all outlets in a city

Filter outlets by user location

Frontend Integration using React

Database Connection via PostgreSQL

🏗 Project Structure

⚙️ Installation & Setup

1️⃣ Backend Setup

Pre-requisites:

Python 3.10+

PostgreSQL Database

pip package manager

Install Dependencies

Configure Environment Variables

Create a .env file inside the backend/ directory and add your database credentials:

Run the Backend Server

The FastAPI backend will be available at http://localhost:8080.

2️⃣ Frontend Setup

Pre-requisites:

Node.js 16+

npm or yarn

Install Dependencies

Run the Frontend

The React frontend will be available at http://localhost:3000.

📡 API Endpoints

📍 Search Subway Outlets

GET /search/?query=<query>&user_id=<user_id>

Example:

🏢 List All Outlets

GET /outlets/

Example:


🕒 Get Outlet Operating Hours

GET /search/?query=what+time+does+subway+close?&user_id=<user_id>

Example:

🐞 Troubleshooting

❌ Database Connection Failed: invalid sslmode value: "required"

Update the .env file and remove sslmode="required" from DB_CONFIG in database.py

❌ Internal Server Error on /outlets/

Ensure PostgreSQL is running and the database credentials in .env are correct.

Check logs in Railway (railway logs).

📌 Deployment

Deploying to Railway

1️⃣ Push Code to GitHub

Ensure your project is in a GitHub repository:

2️⃣ Deploy on Railway

Go to Railway.app

Create a new project

Connect your GitHub repo

Add environment variables in the Railway dashboard

Deploy & test your API!
