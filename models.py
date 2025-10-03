from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime
import enum


# models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime, enum, os

# 讀取環境變數；沒有就退回 /tmp（臨時、非持久）
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/campus_cleaning.db")

connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserRole(str, enum.Enum):
    cleaner = "cleaner"
    maintenance = "maintenance"
    admin = "admin"
    user = "user"

class ReportStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

# （其餘 model 保持不變）


SQLALCHEMY_DATABASE_URL = "sqlite:///./campus_cleaning.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class UserRole(str, enum.Enum):
    cleaner = "cleaner"
    maintenance = "maintenance"
    admin = "admin"
    user = "user"

class ReportStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(Enum(UserRole))

    cleaning_records = relationship("CleaningRecord", back_populates="user")
    repair_reports = relationship("RepairReport", back_populates="reporter")

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    
    cleaning_records = relationship("CleaningRecord", back_populates="location")
    repair_reports = relationship("RepairReport", back_populates="location")

class CleaningRecord(Base):
    __tablename__ = "cleaning_records"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    location = relationship("Location", back_populates="cleaning_records")
    user = relationship("User", back_populates="cleaning_records")

class RepairReport(Base):
    __tablename__ = "repair_reports"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    reported_by_user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(String)
    image_url = Column(String, nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.pending)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    location = relationship("Location", back_populates="repair_reports")
    reporter = relationship("User", back_populates="repair_reports")

