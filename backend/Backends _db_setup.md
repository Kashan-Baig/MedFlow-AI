🏥 MedFlow AI - Backend Setup Guide (Windows)
This guide will help you set up the Python environment and a local PostgreSQL database on Windows.

1. Prerequisites
Python 3.10.x: Download here (Ensure you check the box "Add Python to PATH" during installation).

Git: Download here.

uv: The fastest Python package manager. Open PowerShell and run:

PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
2. Project Setup
Open your terminal (CMD or PowerShell) inside the project folder:

Create Virtual Environment
PowerShell
# Create the environment with the correct version
uv venv --python 3.10

# Activate the environment
.venv\Scripts\activate
Install Dependencies
PowerShell
uv sync
3. Database Setup (PostgreSQL)
Since you don't have "Postgres.app" on Windows, follow these steps:

Download PostgreSQL: Get the Windows installer from EnterpriseDB.

Installation:

During setup, set a password for the postgres user (e.g., root or admin). Remember this password!

Keep the default port 5432.

Create the Database:

Open pgAdmin 4 (installed with Postgres).

Right-click Databases -> Create -> Database...

Name it: medflow_ai_db.

4. Environment Variables (.env)
Create a file named .env in the root folder and paste this. Update the DB password to the one you set in step 3:

Code snippet
DATABASE_URL="postgresql://postgres:YOUR_PASSWORD_HERE@localhost:5432/medflow_ai_db"
SECRET_KEY="your-super-secret-key-change-this-later"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
5. Running the Backend
Ensure your environment is active (.venv\Scripts\activate) and run:

PowerShell
uvicorn main:app --reload
API Docs: Open http://127.0.0.1:8000/docs

Database Tables: They will be created automatically the first time you run the server.

💡 Troubleshooting for Windows
Execution Policy Error: If you can't activate the .venv, run this in PowerShell as Admin:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

psycopg2 error: If you face issues installing the DB driver, ensure you have the Visual C++ Redistributable installed.