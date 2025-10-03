from pydantic import BaseModel
from typing import List, Optional
import datetime
from models import UserRole, ReportStatus

# --- 基本模型 ---
# 用於讀取使用者和地點的基本資訊

class UserBase(BaseModel):
    id: int
    name: str
    role: UserRole

    class Config:
        from_attributes = True

class LocationBase(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# --- 創建資料的模型 ---
# 用於 API 接收創建請求時的資料驗證

class CleaningRecordCreate(BaseModel):
    location_id: int
    user_id: int

class RepairReportCreate(BaseModel):
    location_id: int
    description: str
    reported_by_user_id: int


# --- 更新資料的模型 ---

class RepairReportUpdate(BaseModel):
    status: ReportStatus


# --- 完整的回應模型 ---
# 用於 API 回傳資料給前端時的完整結構

class CleaningRecord(BaseModel):
    id: int
    timestamp: datetime.datetime
    location: LocationBase
    user: UserBase

    class Config:
        from_attributes = True

class RepairReport(BaseModel):
    id: int
    description: str
    image_url: Optional[str] = None
    status: ReportStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    location: LocationBase
    reporter: UserBase

    class Config:
        from_attributes = True

# --- 統計報表的模型 ---

class WeeklyCleaningStat(BaseModel):
    day: str
    count: int

class RepairStatusDistribution(BaseModel):
    pending: int
    in_progress: int
    completed: int

class AdminStats(BaseModel):
    weekly_cleaning: List[WeeklyCleaningStat]
    repair_status_distribution: RepairStatusDistribution
