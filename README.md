# Job Application Tracker

Simple locally-runnable app for tracking job applications.

## Stack
- FastAPI backend
- SQLite database
- SQLAlchemy ORM
- HTML/CSS/JavaScript frontend

## Job fields
- title
- company
- location
- link
- salary
- status
- notes

## Run locally
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start server:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Open http://127.0.0.1:8000

Database file (`jobs.db`) will be created automatically.
