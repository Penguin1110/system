from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime, timedelta

# Corrected Imports: All necessary components are imported from the existing models.py and schemas.py
import models
import schemas
from models import SessionLocal, engine, Base, User, Location, CleaningRecord, RepairReport, UserRole, ReportStatus

# --- Setup ---

# Ensure the 'uploads' directory for images exists
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create all database tables based on the models defined in models.py
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow frontend to communicate with this backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Dependency ---

def get_db():
    """
    This function creates a database session for each API request and ensures it's closed afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Initial Data Population ---

@app.on_event("startup")
def populate_initial_data():
    """
    This function runs once when the server starts.
    It checks if the database is empty and, if so, adds some default users and locations.
    """
    db = SessionLocal()
    if db.query(User).count() == 0:
        # Add default users for each role
        users_data = [
            {"id": 1, "name": "王大明", "role": "cleaner"},
            {"id": 2, "name": "李師傅", "role": "maintenance"},
            {"id": 3, "name": "陳主任", "role": "admin"},
            {"id": 4, "name": "林同學", "role": "user"},
        ]
        for user_data in users_data:
            db.add(User(**user_data))
        
        # Add default locations to clean/report
        locations_data = [
            {"id": 1, "name": "教學大樓 A 座一樓男廁"},
            {"id": 2, "name": "教學大樓 A 座一樓女廁"},
            {"id": 3, "name": "圖書館三樓飲水機"},
            {"id": 4, "name": "體育館入口處洗手間"},
            {"id": 5, "name": "學生宿舍 B 棟二樓公共區域"},
        ]
        for loc_data in locations_data:
            db.add(Location(**loc_data))
        
        db.commit()
    db.close()

# --- API Endpoints ---

# Endpoint to serve uploaded images
@app.get("/uploads/{filename}")
async def get_image(filename: str):
    return FileResponse(f"uploads/{filename}")

# Endpoint to get all available locations
@app.get("/locations", response_model=List[schemas.LocationBase])
def read_locations(db: Session = Depends(get_db)):
    locations = db.query(Location).all()
    return locations

# Endpoint for cleaners to submit a cleaning record
@app.post("/cleaning-records", response_model=schemas.CleaningRecord)
def create_cleaning_record(record: schemas.CleaningRecordCreate, db: Session = Depends(get_db)):
    db_record = CleaningRecord(location_id=record.location_id, user_id=record.user_id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

# Endpoint to view recent cleaning records
@app.get("/cleaning-records", response_model=List[schemas.CleaningRecord])
def read_cleaning_records(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    records = db.query(CleaningRecord).order_by(CleaningRecord.timestamp.desc()).offset(skip).limit(limit).all()
    return records

# Endpoint for anyone to submit a repair report (with an optional image)
@app.post("/repair-reports", response_model=schemas.RepairReport)
async def create_repair_report(
    location_id: int = Form(...),
    description: str = Form(...),
    reported_by_user_id: int = Form(...),
    image: Optional[UploadFile] = File(None), 
    db: Session = Depends(get_db)
):
    image_url = None
    if image:
        # Save the uploaded image and store its path
        file_location = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{image.filename}")
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(image.file, file_object)
        image_url = file_location
    
    db_report = RepairReport(
        location_id=location_id,
        description=description,
        reported_by_user_id=reported_by_user_id,
        image_url=image_url
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# Endpoint to view all repair reports
@app.get("/repair-reports", response_model=List[schemas.RepairReport])
def read_repair_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    reports = db.query(RepairReport).order_by(RepairReport.created_at.desc()).offset(skip).limit(limit).all()
    return reports

# Endpoint for maintenance staff to update the status of a repair report
@app.put("/repair-reports/{report_id}", response_model=schemas.RepairReport)
def update_repair_report(report_id: int, report_update: schemas.RepairReportUpdate, db: Session = Depends(get_db)):
    db_report = db.query(RepairReport).filter(RepairReport.id == report_id).first()
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    
    db_report.status = report_update.status
    db_report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_report)
    return db_report

# Endpoint for admins to get statistical data for the dashboard
@app.get("/admin/stats", response_model=schemas.AdminStats)
def get_admin_stats(db: Session = Depends(get_db)):
    # Calculate cleaning frequency for the current week
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    days_of_week = [(start_of_week + timedelta(days=i)) for i in range(7)]
    
    weekly_cleaning_counts = []
    for day in days_of_week:
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        count = db.query(CleaningRecord).filter(CleaningRecord.timestamp >= day_start, CleaningRecord.timestamp <= day_end).count()
        weekly_cleaning_counts.append({"day": day.strftime('%a'), "count": count})

    # Calculate the distribution of repair report statuses
    pending = db.query(RepairReport).filter(RepairReport.status == ReportStatus.pending).count()
    in_progress = db.query(RepairReport).filter(RepairReport.status == ReportStatus.in_progress).count()
    completed = db.query(RepairReport).filter(RepairReport.status == ReportStatus.completed).count()
    
    repair_distribution = {
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed
    }

    return {
        "weekly_cleaning": weekly_cleaning_counts,
        "repair_status_distribution": repair_distribution
    }

@app.get("/health")
def health():
    return {"ok": True}

from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="static", html=True), name="static")