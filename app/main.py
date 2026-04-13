import logging
import os
from datetime import datetime, timezone

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy import and_
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Job
from .schemas import JobCreate, JobOut, JobUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Job Application Tracker")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

EXTERNAL_JOBS_API_URL = os.getenv(
    "EXTERNAL_JOBS_API_URL",
    "https://jsearch.p.rapidapi.com/search",
)
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "jsearch.p.rapidapi.com")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
DEFAULT_IMPORT_KEYWORDS = [
    "electrical engineer",
    "embedded systems",
    "power electronics",
    "medical instruments",
    "satellite",
]
DEFAULT_IMPORT_LOCATION = os.getenv("IMPORT_LOCATION", "California")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _mock_jobs_payload():
    return [
        {
            "title": "Backend Engineer",
            "company": "Mock Company A",
            "location": "Remote",
            "url": "https://example.com/jobs/backend-engineer",
            "salary": "$120k-$150k",
            "description": "Mocked daily import job.",
        },
        {
            "title": "Frontend Engineer",
            "company": "Mock Company B",
            "location": "San Francisco, CA",
            "url": "https://example.com/jobs/frontend-engineer",
            "salary": "$110k-$140k",
            "description": "Mocked daily import job.",
        },
    ]


async def fetch_jobs(
    keyword: str | None = None,
    keywords: list[str] | None = None,
    location: str | None = None,
):
    search_keywords = keywords or ([keyword] if keyword else DEFAULT_IMPORT_KEYWORDS)
    search_location = location or DEFAULT_IMPORT_LOCATION
    raw_items = []

    try:
        if not RAPIDAPI_KEY:
            raise ValueError("RAPIDAPI_KEY is not configured")

        async with httpx.AsyncClient(timeout=10) as client:
            for search_keyword in search_keywords:
                response = await client.get(
                    EXTERNAL_JOBS_API_URL,
                    params={
                        "query": f"{search_keyword} in {search_location}",
                        "page": "1",
                        "num_pages": "1",
                    },
                    headers={
                        "X-RapidAPI-Key": RAPIDAPI_KEY,
                        "X-RapidAPI-Host": RAPIDAPI_HOST,
                    },
                )
                response.raise_for_status()
                raw_items.extend(response.json().get("data", []))
    except Exception as exc:
        logger.warning("Failed external jobs API fetch, using mock payload: %s", exc)
        raw_items = _mock_jobs_payload()

    db = SessionLocal()
    inserted_count = 0
    try:
        for item in raw_items[:5]:
            title = item.get("job_title") or item.get("title") or "Untitled Job"
            company = item.get("employer_name") or item.get("company") or "Unknown Company"
            location = (
                item.get("job_location")
                or item.get("location")
                or ", ".join(
                    part
                    for part in [item.get("job_city"), item.get("job_state"), item.get("job_country")]
                    if part
                )
                or "Unknown"
            )
            link = (
                item.get("job_apply_link")
                or item.get("job_google_link")
                or item.get("url")
                or f"https://example.com/jobs/{item.get('job_id') or item.get('id', '')}"
            )
            salary = (
                item.get("job_salary")
                or (
                    f"${item.get('job_min_salary', '')}-${item.get('job_max_salary', '')}"
                    if item.get("job_min_salary") or item.get("job_max_salary")
                    else "Not specified"
                )
                or item.get("salary")
                or "Not specified"
            )
            notes = (
                item.get("job_description")
                or item.get("description")
                or f"Imported by background fetch for keywords {search_keywords} in '{search_location}'."
            )

            exists = (
                db.query(Job)
                .filter(and_(Job.title == title, Job.company == company, Job.link == link))
                .first()
            )
            if exists:
                continue

            db.add(
                Job(
                    title=title,
                    company=company,
                    location=location,
                    link=link,
                    salary=salary,
                    status="New",
                    notes=notes,
                )
            )
            inserted_count += 1
            if inserted_count >= 5:
                break

        db.commit()
        logger.info("Daily importer inserted %s new jobs.", inserted_count)
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        fetch_jobs,
        trigger="interval",
        days=1,
        kwargs={
            "keywords": DEFAULT_IMPORT_KEYWORDS,
            "location": DEFAULT_IMPORT_LOCATION,
        },
        id="daily_job_import",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
    app.state.scheduler = scheduler


@app.on_event("shutdown")
async def shutdown_event():
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        scheduler.shutdown(wait=False)


@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/jobs", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.id.desc()).all()


@app.post("/api/jobs/import")
async def import_jobs(keyword: str | None = None, location: str | None = None):
    keyword_list = [k.strip() for k in keyword.split(",")] if keyword else None
    await fetch_jobs(keyword=keyword, keywords=keyword_list, location=location or DEFAULT_IMPORT_LOCATION)
    return {
        "message": "Import completed",
        "keywords": keyword_list or DEFAULT_IMPORT_KEYWORDS,
        "location": location or DEFAULT_IMPORT_LOCATION,
    }


@app.post("/api/jobs", response_model=JobOut)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    db_job = Job(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@app.get("/api/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.put("/api/jobs/{job_id}", response_model=JobOut)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    for key, value in payload.model_dump().items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)
    return job


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}
