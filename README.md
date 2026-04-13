# Job Application Tracker

Simple locally-runnable app for tracking job applications.

## Stack
- FastAPI backend
- SQLite database
- SQLAlchemy ORM
- HTML/CSS/JavaScript frontend
- Daily background importer for new jobs
- APScheduler daily scheduler for automatic imports

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

## Daily background job import
- APScheduler starts with the FastAPI app and runs `fetch_jobs()` once per day.
- It fetches from RapidAPI JSearch (`EXTERNAL_JOBS_API_URL`, default: `https://jsearch.p.rapidapi.com/search`).
- Filtering is supported through keyword(s) and location (manual endpoint query params + `IMPORT_LOCATION`).
- Default daily keyword set:
  - electrical engineer
  - embedded systems
  - power electronics
  - medical instruments
  - satellite
- Default location: California
- If the API call fails, the app uses a small mocked payload.
- Up to 5 new jobs are inserted each day (duplicates are skipped by title/company/link match).

### Optional environment variables
- `RAPIDAPI_KEY`: your RapidAPI key (required for real API fetches)
- `RAPIDAPI_HOST`: defaults to `jsearch.p.rapidapi.com`
- `IMPORT_LOCATION`: default daily fetch location (default: `California`)

### Manual import endpoint
- `POST /api/jobs/import?keyword=electrical+engineer,embedded+systems&location=california`
